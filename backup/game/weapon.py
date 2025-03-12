class Weapon:
    """武器クラス"""
    def __init__(self, name, type, damage, cooldown):
        self.name = name  # 武器の名前
        self.type = type  # 武器の種類（ビーム、弾丸、近接など）
        self.damage = damage  # 武器のダメージ
        self.cooldown = cooldown  # 連射間隔（フレーム数） 