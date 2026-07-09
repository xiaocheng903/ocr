"""
标注文件生成器 — 为每张测试图片生成标准化的 ground truth 标注文件
"""

import json
import os
from datetime import datetime


def build_annotation(profile: dict, doc_type: str, image_file: str,
                     variant_info: dict = None, image_size: tuple = None) -> dict:
    """
    构建单张图片的标注

    Args:
        profile: 候选人档案
        doc_type: 证件类型 (id_card_front, id_card_back, bank_card, education_cert, degree_cert, study_proof, resignation_proof, employment_booklet)
        image_file: 图片文件名
        variant_info: 变异信息 (type, method, ...)
        image_size: (width, height)
    """
    edu = profile.get("education", {})
    emp = profile.get("employment", {})

    annotation = {
        "image": image_file,
        "doc_type": doc_type,
        "variant": variant_info or {},
        "generated_at": datetime.now().isoformat(),
        "ground_truth": {},
    }

    if doc_type in ("id_card_front", "id_card_back"):
        annotation["ground_truth"] = {
            "name": profile["name"],
            "gender": profile["gender"],
            "ethnicity": profile.get("ethnicity", ""),
            "birth_date": profile["birth_date"],
            "address": profile["address"],
            "id_number": profile["id_number"],
        }
    elif doc_type == "bank_card":
        annotation["ground_truth"] = {
            "bank_name": profile["bank_name"],
            "card_number": profile["bank_card"],
            "holder_name": profile["name"],
        }
    elif doc_type == "education_cert":
        annotation["ground_truth"] = {
            "name": profile["name"],
            "gender": profile["gender"],
            "birth_date": profile["birth_date"],
            "university": edu.get("university", ""),
            "major": edu.get("major", ""),
            "level": edu.get("level", ""),
            "start_date": edu.get("start_date", ""),
            "end_date": edu.get("end_date", ""),
            "cert_no": edu.get("cert_no", ""),
        }
    elif doc_type == "degree_cert":
        annotation["ground_truth"] = {
            "name": profile["name"],
            "gender": profile["gender"],
            "birth_date": profile["birth_date"],
            "university": edu.get("university", ""),
            "major": edu.get("major", ""),
            "level": edu.get("level", ""),
            "degree": edu.get("degree", ""),
            "cert_no": edu.get("cert_no", ""),
        }
    elif doc_type == "study_proof":
        annotation["ground_truth"] = {
            "name": profile["name"],
            "gender": profile["gender"],
            "id_number": profile["id_number"],
            "birth_date": profile["birth_date"],
            "university": edu.get("university", ""),
            "major": edu.get("major", ""),
            "level": edu.get("level", ""),
            "start_date": edu.get("start_date", ""),
            "expected_graduation": edu.get("end_date", ""),
            "student_no": edu.get("cert_no", ""),
            "status": "在读",
        }
    elif doc_type == "resignation_proof":
        annotation["ground_truth"] = {
            "name": profile["name"],
            "id_number": profile["id_number"],
            "company": emp.get("company", ""),
            "department": emp.get("department", ""),
            "title": emp.get("title", ""),
            "hire_date": emp.get("hire_date", ""),
            "resign_date": emp.get("resign_date", ""),
        }
    elif doc_type == "employment_booklet":
        annotation["ground_truth"] = {
            "name": profile["name"],
            "gender": profile["gender"],
            "id_number": profile["id_number"],
            "birth_date": profile["birth_date"],
            "education_level": edu.get("level", ""),
            "company": emp.get("company", ""),
            "title": emp.get("title", ""),
            "hire_date": emp.get("hire_date", ""),
            "resign_date": emp.get("resign_date", ""),
        }

    if image_size:
        annotation["image_size"] = {"width": image_size[0], "height": image_size[1]}

    return annotation


def build_manifest(profile: dict, output_dir: str, files: list) -> dict:
    """构建候选人维度的 manifest"""
    return {
        "candidate_id": f"CAND-{datetime.now().strftime('%Y%m%d')}-{profile['name']}",
        "candidate_name": profile["name"],
        "id_number": profile["id_number"],
        "output_dir": output_dir,
        "total_files": len(files),
        "files": files,
        "profile": profile,
    }


def build_summary(profiles: list, total_files: int, output_dir: str) -> dict:
    """构建全局 summary"""
    doc_types = set()
    variant_types = set()
    for p in profiles:
        for f in p.get("files", []):
            doc_types.add(f.get("doc_type", "unknown"))
            if f.get("variant"):
                variant_types.add(f["variant"].get("type", "unknown"))

    return {
        "generated_at": datetime.now().isoformat(),
        "output_dir": output_dir,
        "total_candidates": len(profiles),
        "total_files": total_files,
        "doc_types": sorted(doc_types),
        "variant_types": sorted(variant_types),
        "candidates": [
            {
                "name": p.get("candidate_name", ""),
                "id_number": p.get("id_number", "")[:6] + "****" + p.get("id_number", "")[-4:] if p.get("id_number") else "",
                "files": len(p.get("files", [])),
            }
            for p in profiles
        ],
    }

