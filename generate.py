#!/usr/bin/env python3
"""
OCR 测试数据自动造数 Pipeline

生成流程:
1. 字段值生成 → 候选人档案
2. 标准证件渲染 → 图片
3. 图像变异 → 变体图片
4. 标注文件生成 → JSON

用法:
  python3 generate.py                    # 生成 1 个候选人, 所有证件类型, 不生成变体
  python3 generate.py --count 5          # 生成 5 个候选人
  python3 generate.py --variants         # 生成所有变异变体
  python3 generate.py --variants rotate_small,blur_light  # 仅生成指定变异
  python3 generate.py --seed 42 --out ./output
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime

import numpy as np

# 添加 generators 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from generators.field_generator import FieldGenerator
from generators.image_renderer import IDCardRenderer, BankCardRenderer, CertificateRenderer
from generators.augmentation import AugmentationEngine
from generators.annotation import build_annotation, build_manifest, build_summary


# ── 文档类型定义 ──────────────────────────────────────────
DOC_TYPES = {
    "id_card_front": {
        "name": "身份证(人像面)",
        "renderer": "id_card",
        "method": "render_front",
    },
    "id_card_back": {
        "name": "身份证(国徽面)",
        "renderer": "id_card",
        "method": "render_back",
    },
    "bank_card": {
        "name": "银行卡",
        "renderer": "bank_card",
        "method": "render",
    },
    "education_cert": {
        "name": "学历证书",
        "renderer": "cert",
        "method": "render_education",
    },
    "degree_cert": {
        "name": "学位证书",
        "renderer": "cert",
        "method": "render_degree",
    },
    "study_proof": {
        "name": "在读证明",
        "renderer": "cert",
        "method": "render_study_proof",
    },
    "resignation_proof": {
        "name": "离职证明",
        "renderer": "cert",
        "method": "render_resignation_proof",
    },
    "employment_booklet": {
        "name": "劳动手册",
        "renderer": "cert",
        "method": "render_employment_booklet",
    },
}


def main():
    parser = argparse.ArgumentParser(
        description="OCR 测试数据自动造数工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s                                    # 默认: 1人, 全部证件, 无变异
  %(prog)s --count 10 --seed 42               # 10人, 固定种子
  %(prog)s --variants                          # 全部变异类型
  %(prog)s --variants rotate_small,blur_light  # 仅指定变异
  %(prog)s --no-standard                       # 仅生成非标准 PDF (images/non_standard)
  %(prog)s --docs id_card_front,bank_card      # 仅指定证件类型
  %(prog)s --name 张三 --id 110101199001011234  # 指定姓名和身份证号
  %(prog)s --docs resignation_proof --resign-date 2026-06-30  # 指定离职日期
  %(prog)s --count 3                           # 不传姓名/身份证号时随机生成
  %(prog)s --name 张三 --id 110101199001011234 --count 3  # 用同一身份生成多份
  %(prog)s --invalid-id                        # 生成校验位错误的身份证号
        """,
    )
    parser.add_argument("--count", type=int, default=1,
                        help="生成候选人数量 (默认: 1)")
    parser.add_argument("--seed", type=int, default=None,
                        help="随机种子 (默认: 当前时间戳)")
    parser.add_argument("--out", type=str, default="output",
                        help="输出目录 (默认: ./output)")
    parser.add_argument("--name", type=str, default=None,
                        help="指定姓名（不传则随机生成）")
    parser.add_argument("--id", "--id-number", type=str, default=None, dest="id_number",
                        help="指定身份证号 (18位, 最后一位可为X；不传则随机生成)")
    parser.add_argument("--resign-date", type=str, default=None,
                        help="指定离职日期 (YYYY-MM-DD，仅覆盖离职相关文档日期)")
    parser.add_argument("--invalid-id", action="store_true",
                        help="生成校验位错误的身份证号")
    parser.add_argument("--rare-name", action="store_true",
                        help="生成含生僻字的姓名")
    parser.add_argument("--ethnic-name", action="store_true",
                        help="生成少数民族姓名")
    parser.add_argument("--docs", type=str, default=None,
                        help="证件类型, 逗号分隔 (默认: 全部)")
    parser.add_argument("--variants", type=str, default=None, nargs="?",
                        const="__ALL__",
                        help="变异类型, 逗号分隔, 不指定则生成全部 (默认: 不生成变异)")
    parser.add_argument("--no-standard", action="store_true",
                        help="不生成标准图片，改为生成非标准 PDF 到 images/non_standard")
    parser.add_argument("--format", type=str, default="png",
                        choices=["png", "jpg"],
                        help="输出图片格式 (默认: png)")
    parser.add_argument("--quality", type=int, default=95,
                        help="JPEG 质量 (默认: 95)")

    args = parser.parse_args()

    # ── 参数校验/归一化 ───────────────────────────────
    if args.name is not None:
        args.name = args.name.strip()
        if not args.name:
            print("[错误] --name 不能为空")
            sys.exit(1)

    if args.id_number is not None:
        args.id_number = args.id_number.strip().upper()
        if not re.fullmatch(r"\d{17}[\dX]", args.id_number):
            print("[错误] --id/--id-number 格式无效，应为18位身份证号（最后一位可为X）")
            sys.exit(1)

    if args.resign_date is not None:
        args.resign_date = args.resign_date.strip()
        try:
            datetime.strptime(args.resign_date, "%Y-%m-%d")
        except ValueError:
            print("[错误] --resign-date 格式无效，应为 YYYY-MM-DD")
            sys.exit(1)

    if args.invalid_id and args.id_number:
        print("[错误] --invalid-id 不能与 --id/--id-number 同时使用")
        sys.exit(1)

    # ── 初始化 ───────────────────────────────────────
    seed = args.seed if args.seed is not None else int(datetime.now().timestamp())
    print(f"[初始化] 随机种子: {seed}")

    field_gen = FieldGenerator(seed=seed)
    np_rng = np.random.RandomState(seed)

    id_renderer = IDCardRenderer(np_rng)
    bank_renderer = BankCardRenderer(np_rng)
    cert_renderer = CertificateRenderer(np_rng)
    aug_engine = AugmentationEngine(np_rng)

    # ── 证件类型过滤 ─────────────────────────────────
    if args.docs:
        selected_docs = {k: v for k, v in DOC_TYPES.items() if k in args.docs.split(",")}
        if not selected_docs:
            print(f"[错误] 无效的证件类型: {args.docs}")
            print(f"  可用类型: {', '.join(DOC_TYPES.keys())}")
            sys.exit(1)
    else:
        selected_docs = DOC_TYPES

    # ── 变异类型 ─────────────────────────────────────
    if args.variants == "__ALL__":
        variant_names = None  # None = 全部
    elif args.variants:
        variant_names = [v.strip() for v in args.variants.split(",")]
    else:
        variant_names = []  # 空列表 = 不生成变异

    # ── 输出目录 ─────────────────────────────────────
    out_dir = os.path.abspath(args.out)
    os.makedirs(out_dir, exist_ok=True)

    # ── 主循环: 逐个候选人生成 ───────────────────────
    all_profiles = []
    total_files = 0

    for i in range(1, args.count + 1):
        # 生成候选人档案
        if args.rare_name:
            profile = field_gen.generate_profile()
            profile["name"] = field_gen.generate_rare_name()
        elif args.ethnic_name:
            profile = field_gen.generate_profile()
            profile["name"] = field_gen.generate_ethnic_name()
        elif args.name or args.id_number:
            profile = field_gen.generate_profile(
                name=args.name,
                id_number=args.id_number,
            )
        else:
            profile = field_gen.generate_profile()

        if args.invalid_id:
            profile["id_number"] = field_gen.generate_invalid_id_number()
        if args.resign_date:
            profile["employment"]["resign_date"] = args.resign_date

        # 候选人目录
        safe_name = profile["name"].replace(" ", "_").replace("/", "_")
        candidate_dir = os.path.join(out_dir, f"{i:02d}_{safe_name}")
        images_dir = os.path.join(candidate_dir, "images")
        json_dir = os.path.join(candidate_dir, "json")
        standard_image_dir = os.path.join(images_dir, "standard")
        variants_image_dir = os.path.join(images_dir, "variants")
        non_standard_image_dir = os.path.join(images_dir, "non_standard")
        standard_json_dir = os.path.join(json_dir, "standard")
        variants_json_dir = os.path.join(json_dir, "variants")
        non_standard_json_dir = os.path.join(json_dir, "non_standard")
        if args.no_standard:
            os.makedirs(non_standard_image_dir, exist_ok=True)
            os.makedirs(non_standard_json_dir, exist_ok=True)
        else:
            os.makedirs(standard_image_dir, exist_ok=True)
            os.makedirs(standard_json_dir, exist_ok=True)

        files_manifest = []

        print(f"\n[候选人 {i}/{args.count}] {profile['name']} ({profile['id_number']})")

        # ── 渲染标准证件 ─────────────────────────────
        for doc_key, doc_info in selected_docs.items():
            renderer_name = doc_info["renderer"]
            method_name = doc_info["method"]

            if renderer_name == "id_card":
                renderer = id_renderer
            elif renderer_name == "bank_card":
                renderer = bank_renderer
            else:
                renderer = cert_renderer

            method = getattr(renderer, method_name)
            img = method(profile)
            img_size = img.size

            if args.no_standard:
                # 保存非标准 PDF 版本
                filename = f"{doc_key}.pdf"
                filepath = os.path.join(non_standard_image_dir, filename)
                pdf_img = img.convert("RGB") if img.mode != "RGB" else img
                pdf_img.save(filepath, "PDF")
                total_files += 1

                ann = build_annotation(profile, doc_key, filename, image_size=img_size)
                ann_path = os.path.join(non_standard_json_dir, f"{doc_key}.json")
                with open(ann_path, "w", encoding="utf-8") as f:
                    json.dump(ann, f, ensure_ascii=False, indent=2)

                files_manifest.append({
                    "doc_type": doc_key,
                    "doc_name": doc_info["name"],
                    "file": f"images/non_standard/{filename}",
                    "annotation": f"json/non_standard/{os.path.basename(ann_path)}",
                    "variant": None,
                })
                print(f"  ✓ {doc_info['name']} (non_standard/pdf)")
            else:
                # 保存标准版本
                filename = f"{doc_key}.{args.format}"
                filepath = os.path.join(standard_image_dir, filename)
                img.save(filepath, quality=args.quality)
                total_files += 1

                # 生成标注
                ann = build_annotation(profile, doc_key, filename, image_size=img_size)
                ann_path = os.path.join(standard_json_dir, f"{doc_key}.json")
                with open(ann_path, "w", encoding="utf-8") as f:
                    json.dump(ann, f, ensure_ascii=False, indent=2)

                files_manifest.append({
                    "doc_type": doc_key,
                    "doc_name": doc_info["name"],
                    "file": f"images/standard/{filename}",
                    "annotation": f"json/standard/{os.path.basename(ann_path)}",
                    "variant": None,
                })
                print(f"  ✓ {doc_info['name']}")

            # ── 生成变异版本 ──────────────────────────
            if variant_names or variant_names is None:
                os.makedirs(variants_image_dir, exist_ok=True)
                os.makedirs(variants_json_dir, exist_ok=True)
                doc_variants_image_dir = os.path.join(variants_image_dir, doc_key)
                doc_variants_json_dir = os.path.join(variants_json_dir, doc_key)
                os.makedirs(doc_variants_image_dir, exist_ok=True)
                os.makedirs(doc_variants_json_dir, exist_ok=True)

                if variant_names is None:
                    variants = aug_engine.apply_all_variants(img)
                else:
                    variants = aug_engine.apply_selected_variants(img, variant_names)

                for v_img, v_meta in variants:
                    v_type = v_meta.get("type", "unknown")
                    v_method = v_meta.get("method", "unknown")
                    v_filename = f"{doc_key}_{v_type}_{v_method}.{args.format}"
                    v_filepath = os.path.join(doc_variants_image_dir, v_filename)

                    # 避免文件名冲突
                    counter = 1
                    while os.path.exists(v_filepath):
                        v_filename = f"{doc_key}_{v_type}_{v_method}_{counter}.{args.format}"
                        v_filepath = os.path.join(doc_variants_image_dir, v_filename)
                        counter += 1

                    v_img.save(v_filepath, quality=args.quality)
                    total_files += 1

                    # 变异版本标注 = 原标注 + 变异信息
                    v_ann = build_annotation(profile, doc_key, v_filename,
                                            variant_info=v_meta, image_size=v_img.size)
                    v_ann_path = os.path.join(doc_variants_json_dir, v_filename.rsplit(".", 1)[0] + ".json")
                    with open(v_ann_path, "w", encoding="utf-8") as f:
                        json.dump(v_ann, f, ensure_ascii=False, indent=2)

                    files_manifest.append({
                        "doc_type": doc_key,
                        "doc_name": doc_info["name"],
                        "file": f"images/variants/{doc_key}/{v_filename}",
                        "annotation": f"json/variants/{doc_key}/{os.path.basename(v_ann_path)}",
                        "variant": v_meta,
                    })

                print(f"     ↳ {len(variants)} 个变异版本")

        # ── 保存 profile ─────────────────────────────
        profile_path = os.path.join(json_dir, "profile.json")
        os.makedirs(json_dir, exist_ok=True)
        with open(profile_path, "w", encoding="utf-8") as f:
            json.dump(profile, f, ensure_ascii=False, indent=2)

        # ── 保存 manifest ────────────────────────────
        manifest = build_manifest(profile, candidate_dir, files_manifest)
        manifest_path = os.path.join(json_dir, "manifest.json")
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)

        all_profiles.append(manifest)

    # ── 保存全局 summary ─────────────────────────────
    summary = build_summary(all_profiles, total_files, out_dir)
    summary_json_dir = os.path.join(out_dir, "json")
    os.makedirs(summary_json_dir, exist_ok=True)
    summary_path = os.path.join(summary_json_dir, "_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    # ── 输出摘要 ─────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"[完成] 输出目录: {out_dir}")
    print(f"  候选人: {args.count} 人")
    print(f"  证件类型: {len(selected_docs)} 种")
    print(f"  总文件数: {total_files}")
    print(f"  随机种子: {seed}")
    print(f"  摘要文件: {summary_path}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()










