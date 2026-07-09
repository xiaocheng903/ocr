"""
字段值生成器 — 按规则生成身份证号、姓名、银行卡号、地址等真实合法字段值。
所有数据均为符合编码规则的虚构数据，仅供测试使用。
"""

import random
from datetime import datetime, timedelta

# ── 姓名库 ──────────────────────────────────────────────
SURNAMES = [
    "赵", "钱", "孙", "李", "周", "吴", "郑", "王", "冯", "陈", "褚", "卫",
    "蒋", "沈", "韩", "杨", "朱", "秦", "尤", "许", "何", "吕", "施", "张",
    "孔", "曹", "严", "华", "金", "魏", "陶", "姜", "戚", "谢", "邹", "喻",
    "柏", "水", "窦", "章", "云", "苏", "潘", "葛", "奚", "范", "彭", "郎",
    "鲁", "韦", "昌", "马", "苗", "凤", "花", "方", "俞", "任", "袁", "柳",
    "丰", "鲍", "史", "唐", "费", "廉", "岑", "薛", "雷", "贺", "倪", "汤",
    "滕", "殷", "罗", "毕", "郝", "邬", "安", "常", "乐", "于", "时", "傅",
    "皮", "卞", "齐", "康", "伍", "余", "元", "卜", "顾", "孟", "平", "黄",
    "穆", "萧", "尹", "姚", "邵", "湛", "汪", "祁", "毛", "禹", "狄", "米",
    "贝", "明", "臧", "计", "伏", "成", "戴", "谈", "宋", "茅", "庞", "熊",
    "纪", "舒", "屈", "项", "祝", "董", "梁", "杜", "阮", "蓝", "闵", "席",
    "季", "麻", "强", "贾", "路", "娄", "危", "江", "童", "颜", "郭", "梅",
    "盛", "林", "刁", "钟", "徐", "邱", "骆", "高", "夏", "蔡", "田", "樊",
    "胡", "凌", "霍", "虞", "万", "支", "柯", "昝", "管", "卢", "莫", "经",
    "房", "裘", "缪", "干", "解", "应", "宗", "丁", "宣", "贲", "邓", "郁",
    "单", "杭", "洪", "包", "诸", "左", "石", "崔", "吉", "钮", "龚", "程",
    "嵇", "邢", "滑", "裴", "陆", "荣", "翁", "荀", "羊", "于", "惠", "甄",
    "曲", "封", "芮", "羿", "储", "靳", "汲", "邴", "糜", "松", "井", "段",
    "富", "巫", "乌", "焦", "巴", "弓", "牧", "隗", "山", "谷", "车", "侯",
    "宓", "蓬", "全", "郗", "班", "仰", "秋", "仲", "伊", "宫", "宁", "仇",
    "栾", "暴", "甘", "钭", "厉", "戎", "祖", "武", "符", "刘", "景", "詹",
    "束", "龙", "叶", "幸", "司", "韶", "郜", "黎", "蓟", "薄", "印", "白",
    "怀", "蒲", "邰", "从", "鄂", "索", "咸", "籍", "赖", "卓", "蔺", "屠",
    "池", "乔", "阴", "郁", "胥", "能", "苍", "双", "闻", "莘", "党", "翟",
    "谭", "贡", "劳", "逄", "姬", "申", "扶", "堵", "冉", "宰", "郦", "雍",
    "璩", "桑", "桂", "濮", "牛", "寿", "通", "边", "扈", "燕", "冀", "浦",
    "尚", "农", "温", "别", "庄", "晏", "柴", "瞿", "阎", "充", "慕", "连",
    "茹", "习", "宦", "艾", "鱼", "容", "向", "古", "易", "慎", "戈", "廖",
    "庚", "终", "暨", "居", "衡", "步", "都", "耿", "满", "弘", "匡", "国",
    "文", "寇", "广", "禄", "阙", "东", "欧", "殳", "沃", "利", "蔚", "越",
    "夔", "隆", "师", "巩", "厍", "聂", "晁", "勾", "敖", "融", "冷", "訾",
    "辛", "阚", "那", "简", "饶", "空", "曾", "毋", "沙", "乜", "养", "鞠",
    "须", "丰", "巢", "关", "蒯", "相", "查", "荆", "红", "游", "竺", "权",
    "逯", "盖", "益", "桓", "公", "万俟", "司马", "上官", "欧阳", "夏侯",
    "诸葛", "闻人", "东方", "赫连", "皇甫", "尉迟", "公羊", "澹台", "公冶",
    "宗政", "濮阳", "淳于", "单于", "太叔", "申屠", "公孙", "仲孙", "轩辕",
    "令狐", "钟离", "宇文", "长孙", "慕容", "司徒", "司空",
]

GIVEN_NAMES_MALE = [
    "伟", "强", "磊", "洋", "勇", "军", "杰", "涛", "明", "超",
    "秀英", "华", "慧", "鑫", "桂英", "建军", "建华", "志强", "文博",
    "俊杰", "浩然", "子涵", "宇轩", "梓豪", "一鸣", "天宇", "浩宇",
    "奕辰", "思远", "铭泽", "博文", "鸿飞", "致远", "晟睿", "子轩",
]

GIVEN_NAMES_FEMALE = [
    "芳", "敏", "静", "丽", "婷", "雪", "玲", "萍", "红", "霞",
    "欣怡", "雨涵", "梓涵", "诗涵", "梦琪", "嘉懿", "煜婷", "婉婷",
    "若曦", "紫萱", "思颖", "语嫣", "晓彤", "悦然", "静怡", "清雅",
    "雅静", "佳琪", "欣妍", "妙彤", "念薇", "碧萱", "夏岚", "怜梦",
]

# 生僻字（用于测试 OCR 对生僻字的识别能力）
RARE_CHARS = ["𬱖", "𬎆", "𬜬", "䶮", "𣲗", "𣲘", "𤆵", "𨱏", "𬭎", "𬀩"]

# 少数民族姓名
ETHNIC_NAMES = [
    "买买提·阿不都热依木",
    "阿依古丽·吐尔逊",
    "巴特尔·乌力吉",
    "卓玛·次仁",
    "阿卜杜拉·麦麦提",
]

# ── 地区码库（真实行政区划前6位） ─────────────────────
AREA_CODES = [
    "110101", "110102", "110105", "110108",  # 北京
    "310101", "310104", "310105", "310115",  # 上海
    "440103", "440104", "440105", "440106",  # 广州
    "440303", "440304", "440305", "440306",  # 深圳
    "330102", "330103", "330104", "330106",  # 杭州
    "320102", "320104", "320105", "320106",  # 南京
    "510104", "510105", "510106", "510107",  # 成都
    "420102", "420103", "420104", "420106",  # 武汉
    "610102", "610103", "610104", "610113",  # 西安
    "500103", "500105", "500106", "500107",  # 重庆
]

# ── 地址库 ──────────────────────────────────────────────
ADDRESS_TEMPLATES = [
    "{}省{}市{}区{}路{}号",
    "{}省{}市{}区{}街道{}号{}室",
    "{}省{}市{}区{}镇{}村{}号",
    "{}市{}区{}路{}弄{}号{}室",
    "{}省{}市{}区{}街道{}小区{}栋{}室",
]

PROVINCES = [
    "北京", "上海", "广东", "浙江", "江苏", "四川", "湖北", "陕西",
    "福建", "山东", "河南", "湖南", "河北", "辽宁", "安徽", "重庆",
]

CITIES = {
    "北京": ["北京市"],
    "上海": ["上海市"],
    "广东": ["广州市", "深圳市", "东莞市", "佛山市"],
    "浙江": ["杭州市", "宁波市", "温州市"],
    "江苏": ["南京市", "苏州市", "无锡市"],
    "四川": ["成都市", "绵阳市"],
    "湖北": ["武汉市", "宜昌市"],
    "陕西": ["西安市", "咸阳市"],
    "福建": ["福州市", "厦门市"],
    "山东": ["济南市", "青岛市"],
    "河南": ["郑州市", "洛阳市"],
    "湖南": ["长沙市", "株洲市"],
    "河北": ["石家庄市", "唐山市"],
    "辽宁": ["沈阳市", "大连市"],
    "安徽": ["合肥市", "芜湖市"],
    "重庆": ["重庆市"],
}

DISTRICTS = {
    "北京市": ["东城区", "西城区", "朝阳区", "海淀区", "丰台区"],
    "上海市": ["黄浦区", "徐汇区", "长宁区", "静安区", "浦东新区"],
    "广州市": ["越秀区", "海珠区", "荔湾区", "天河区", "白云区"],
    "深圳市": ["罗湖区", "福田区", "南山区", "宝安区", "龙岗区"],
    "杭州市": ["上城区", "拱墅区", "西湖区", "滨江区", "余杭区"],
    "南京市": ["玄武区", "秦淮区", "建邺区", "鼓楼区", "栖霞区"],
    "成都市": ["锦江区", "青羊区", "金牛区", "武侯区", "成华区"],
    "武汉市": ["江岸区", "江汉区", "硚口区", "汉阳区", "武昌区"],
    "西安市": ["新城区", "碑林区", "莲湖区", "雁塔区", "未央区"],
    "重庆市": ["渝中区", "江北区", "沙坪坝区", "九龙坡区", "南岸区"],
    "苏州市": ["姑苏区", "虎丘区", "吴中区", "相城区"],
    "厦门市": ["思明区", "湖里区", "集美区", "海沧区"],
    "济南市": ["历下区", "市中区", "槐荫区", "天桥区"],
    "郑州市": ["中原区", "二七区", "管城回族区", "金水区"],
    "长沙市": ["芙蓉区", "天心区", "岳麓区", "开福区"],
    "石家庄市": ["长安区", "桥西区", "新华区", "裕华区"],
    "沈阳市": ["和平区", "沈河区", "大东区", "皇姑区"],
    "合肥市": ["瑶海区", "庐阳区", "蜀山区", "包河区"],
}

STREETS = ["中山", "人民", "解放", "建设", "和平", "光明", "新华", "文化", "科技", "高新"]

# ── 银行卡 ──────────────────────────────────────────────
BANK_BINS = {
    "中国工商银行": ["622202", "622203", "622208"],
    "中国农业银行": ["622848", "622845", "622846"],
    "中国银行": ["621661", "621663", "621666"],
    "中国建设银行": ["622700", "622280", "622966"],
    "招商银行": ["622588", "622580", "622598"],
    "交通银行": ["622262", "622260"],
    "浦发银行": ["622521", "622522"],
    "兴业银行": ["622908", "622909"],
    "中信银行": ["622690", "622691"],
    "民生银行": ["622622", "622615"],
    "光大银行": ["622660", "622662"],
    "平安银行": ["622298", "622536"],
}

# ── 学历/学位 ───────────────────────────────────────────
EDUCATION_LEVELS = [
    ("专科", "大专"),
    ("本科", "学士"),
    ("硕士研究生", "硕士"),
    ("博士研究生", "博士"),
]

MAJORS = [
    "计算机科学与技术", "软件工程", "信息管理与信息系统",
    "金融学", "会计学", "统计学", "工商管理",
    "法学", "汉语言文学", "英语", "数学与应用数学",
    "机械工程", "电气工程及其自动化", "土木工程",
    "临床医学", "护理学", "药学",
]

UNIVERSITIES = [
    "清华大学", "北京大学", "复旦大学", "上海交通大学",
    "浙江大学", "南京大学", "武汉大学", "西安交通大学",
    "中山大学", "四川大学", "华中科技大学", "同济大学",
    "北京航空航天大学", "中国科学技术大学", "哈尔滨工业大学",
    "东南大学", "天津大学", "南开大学", "厦门大学",
    "北京理工大学", "华南理工大学", "大连理工大学", "山东大学",
]

# ── 公司/职位 ───────────────────────────────────────────
COMPANIES = [
    "阿里巴巴（中国）有限公司", "腾讯科技（深圳）有限公司",
    "字节跳动科技有限公司", "美团点评科技有限公司",
    "百度在线网络技术（北京）有限公司", "京东集团股份有限公司",
    "网易（杭州）网络有限公司", "小米科技有限责任公司",
    "华为技术有限公司", "联想集团有限公司",
    "深圳市大疆创新科技有限公司", "比亚迪股份有限公司",
]

TITLES = [
    "软件工程师", "高级工程师", "技术经理", "产品经理",
    "数据分析师", "运营专员", "人力资源专员", "财务主管",
    "市场经理", "销售总监", "项目经理", "架构师",
]


class FieldGenerator:
    """生成符合规则的真实合法字段值"""

    def __init__(self, seed: int = None):
        self.rng = random.Random(seed)

    # ── 基础生成方法 ─────────────────────────────────
    def _randint(self, a: int, b: int) -> int:
        return self.rng.randint(a, b)

    def _pick(self, items: list):
        return self.rng.choice(items)

    def _rand_digits(self, n: int) -> str:
        return "".join(str(self._randint(0, 9)) for _ in range(n))

    # ── 身份证号 ─────────────────────────────────────
    def generate_id_number(self, birth_date: datetime = None) -> str:
        """生成合法 18 位身份证号（含校验位）"""
        if birth_date is None:
            # 随机出生日期：1985-2003
            start = datetime(1985, 1, 1)
            end = datetime(2003, 12, 31)
            delta = (end - start).days
            birth_date = start + timedelta(days=self._randint(0, delta))

        area = self._pick(AREA_CODES)
        y = birth_date.strftime("%Y")
        m = birth_date.strftime("%m")
        d = birth_date.strftime("%d")
        seq = str(self._randint(1, 999)).zfill(3)

        body = area + y + m + d + seq

        # 计算校验位
        weights = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
        check_map = "10X98765432"
        total = sum(int(body[i]) * weights[i] for i in range(17))
        check = check_map[total % 11]

        return body + check

    def generate_invalid_id_number(self) -> str:
        """生成校验位错误的身份证号（用于测试异常检测）"""
        valid = self.generate_id_number()
        # 替换最后一位使校验位错误
        last = valid[-1]
        chars = "0123456789X"
        wrong = self._pick([c for c in chars if c != last])
        return valid[:-1] + wrong

    # ── 姓名 ─────────────────────────────────────────
    def generate_name(self, gender: str = None) -> str:
        """生成中文姓名"""
        if gender is None:
            gender = self._pick(["male", "female"])
        surname = self._pick(SURNAMES)
        if gender == "male":
            given = self._pick(GIVEN_NAMES_MALE)
        else:
            given = self._pick(GIVEN_NAMES_FEMALE)
        return surname + given

    def generate_rare_name(self) -> str:
        """生成含生僻字的姓名"""
        surname = self._pick(SURNAMES)
        rare = self._pick(RARE_CHARS)
        return surname + rare

    def generate_ethnic_name(self) -> str:
        """生成少数民族姓名"""
        return self._pick(ETHNIC_NAMES)

    # ── 地址 ─────────────────────────────────────────
    def generate_address(self) -> str:
        """生成中文地址"""
        province = self._pick(PROVINCES)
        city = self._pick(CITIES[province])
        district = self._pick(DISTRICTS.get(city, ["市中心区"]))
        street = self._pick(STREETS)
        road_no = str(self._randint(1, 999))
        sub_no = str(self._randint(1, 200))

        template = self._pick(ADDRESS_TEMPLATES)
        # 根据模板填充
        addr = template.format(
            province, city, district, street, road_no,
            sub_no, str(self._randint(101, 2008)),
            str(self._randint(1, 30))
        )
        # 处理多余占位符
        while "{}" in addr:
            addr = addr.replace("{}", str(self._randint(1, 100)), 1)
        return addr

    # ── 银行卡号 ─────────────────────────────────────
    @staticmethod
    def _luhn_checksum(partial: str) -> str:
        """Luhn 算法计算校验位"""
        digits = [int(c) for c in partial]
        parity = (len(digits) + 1) % 2
        total = 0
        for i, d in enumerate(digits):
            if i % 2 == parity:
                d *= 2
                if d > 9:
                    d -= 9
            total += d
        return str((10 - (total % 10)) % 10)

    def generate_bank_card(self, bank_name: str = None) -> tuple:
        """返回 (银行名, 卡号)"""
        if bank_name is None:
            bank_name = self._pick(list(BANK_BINS.keys()))
        prefix = self._pick(BANK_BINS[bank_name])
        body_len = 19 - len(prefix) - 1  # 19位卡号
        body = self._rand_digits(body_len)
        partial = prefix + body
        check = self._luhn_checksum(partial)
        return bank_name, partial + check

    # ── 学历信息 ─────────────────────────────────────
    def generate_education(self) -> dict:
        """生成学历信息"""
        level_cn, degree_cn = self._pick(EDUCATION_LEVELS)
        major = self._pick(MAJORS)
        university = self._pick(UNIVERSITIES)
        start_year = self._randint(2006, 2021)
        end_year = start_year + (3 if "专科" in level_cn else 4)
        return {
            "level": level_cn,
            "degree": degree_cn,
            "major": major,
            "university": university,
            "start_date": f"{start_year}-09-01",
            "end_date": f"{end_year}-06-30",
            "cert_no": f"{start_year}{self._rand_digits(6)}",
        }

    # ── 工作经历 ─────────────────────────────────────
    def generate_employment(self) -> dict:
        """生成工作经历"""
        company = self._pick(COMPANIES)
        title = self._pick(TITLES)
        # 入职时间: 2015-2025
        hire_year = self._randint(2015, 2025)
        hire_month = self._randint(1, 12)
        hire_day = self._randint(1, 28)
        hire_date = f"{hire_year}-{hire_month:02d}-{hire_day:02d}"

        # 离职时间: 入职后 1-5 年
        resign_year = hire_year + self._randint(1, 5)
        resign_month = self._randint(1, 12)
        resign_day = self._randint(1, 28)
        resign_date = f"{resign_year}-{resign_month:02d}-{resign_day:02d}"

        return {
            "company": company,
            "title": title,
            "hire_date": hire_date,
            "resign_date": resign_date,
            "department": self._pick(["技术部", "产品部", "数据部", "运营部", "财务部"]),
        }

    # ── 完整候选人档案 ───────────────────────────────
    def generate_profile(self, name: str = None, id_number: str = None) -> dict:
        """生成完整候选人档案"""
        gender = self._pick(["男", "女"])
        if name is None:
            name = self.generate_name("male" if gender == "男" else "female")
        if id_number is None:
            id_number = self.generate_id_number()

        education = self.generate_education()
        employment = self.generate_employment()
        bank_name, bank_card = self.generate_bank_card()

        # 从身份证号提取出生日期
        birth = f"{id_number[6:10]}-{id_number[10:12]}-{id_number[12:14]}"

        return {
            "name": name,
            "gender": gender,
            "ethnicity": self._pick(["汉族", "回族", "维吾尔族", "壮族", "蒙古族"]),
            "id_number": id_number,
            "birth_date": birth,
            "address": self.generate_address(),
            "education": education,
            "employment": employment,
            "bank_name": bank_name,
            "bank_card": bank_card,
            "phone": "1" + self._rand_digits(10),
        }


# ── 快速测试 ──────────────────────────────────────────
if __name__ == "__main__":
    gen = FieldGenerator(seed=42)
    for i in range(3):
        p = gen.generate_profile()
        print(f"\n=== 候选人 {i+1} ===")
        for k, v in p.items():
            print(f"  {k}: {v}")
