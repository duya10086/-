# -*- coding: utf-8 -*-
"""封面排版 + PNG 角色卡打包（纯标准库写 tEXt 块，不依赖扩展）"""
import os, io, json, base64, struct, zlib
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output")
SRC = os.path.join(ROOT, "cover", "Vertical_character_card_cover__2026-11-22T08-08-17.png")
COVER = os.path.join(ROOT, "无界-封面.png")
CARD_JSON = os.path.join(ROOT, "无界-开放世界引擎-v1.0.json")
CARD_PNG = os.path.join(ROOT, "无界-开放世界引擎-v1.0.png")

W, H = 512, 768
F_TITLE = "C:/Windows/Fonts/msyhbd.ttc"
F_TEXT = "C:/Windows/Fonts/msyh.ttc"
F_LATIN = "C:/Windows/Fonts/bahnschrift.ttf"

CYAN = (126, 214, 255)
AMBER = (255, 196, 106)
WHITE = (238, 244, 255)
MUTED = (150, 172, 205)


def spaced(draw, xy, text, font, fill, gap=8, anchor_center_x=None):
    """带字距的文本，anchor_center_x 给定时整体居中"""
    widths = [draw.textlength(ch, font=font) for ch in text]
    total = sum(widths) + gap * (len(text) - 1)
    x = anchor_center_x - total / 2 if anchor_center_x is not None else xy[0]
    y = xy[1]
    for ch, w in zip(text, widths):
        draw.text((x, y), ch, font=font, fill=fill, anchor="ls")
        x += w + gap
    return total


def main():
    im = Image.open(SRC).convert("RGB").resize((W, H), Image.LANCZOS)

    # 底部压暗：让标题可读，同时压掉右下角水印
    grad = Image.new("L", (1, H), 0)
    for y in range(H):
        if y < 400:
            v = 0
        else:
            v = int(242 * ((y - 400) / (H - 400)) ** 1.3)
        grad.putpixel((0, y), min(v, 248))
    black = Image.new("RGB", (W, H), (4, 5, 12))
    im = Image.composite(black, im, grad.resize((W, H)))

    # 最底部再压一层，彻底盖掉原图角标
    bot = Image.new("L", (1, H), 0)
    for y in range(H):
        bot.putpixel((0, y), 0 if y < 690 else min(252, int(252 * ((y - 690) / 78) ** 0.8)))
    im = Image.composite(black, im, bot.resize((W, H)))

    # 顶部压暗一点，放小标签
    topg = Image.new("L", (1, H), 0)
    for y in range(160):
        topg.putpixel((0, y), int(90 * (1 - y / 160)))
    im = Image.composite(black, im, topg.resize((W, H)))

    d = ImageDraw.Draw(im)

    # 外框
    d.rounded_rectangle([10, 10, W - 11, H - 11], radius=14, outline=(120, 180, 255), width=2)
    d.rounded_rectangle([17, 17, W - 18, H - 18], radius=10, outline=(90, 130, 190), width=1)

    # 顶部标签
    f_tag = ImageFont.truetype(F_LATIN, 13)
    d.text((34, 34), "ROLE CARD", font=f_tag, fill=MUTED, anchor="lt")
    d.text((W - 34, 34), "开放世界 · 通用", font=ImageFont.truetype(F_TEXT, 13), fill=MUTED, anchor="rt")

    # 标题
    f_title = ImageFont.truetype(F_TITLE, 118)
    spaced(d, (0, 588), "无界", f_title, WHITE, gap=15, anchor_center_x=W / 2)

    # 副标题 + 两侧细线
    f_sub = ImageFont.truetype(F_TEXT, 26)
    sub = "开 放 世 界 引 擎"
    tw = d.textlength(sub, font=f_sub)
    d.text((W / 2, 628), sub, font=f_sub, fill=(190, 220, 255), anchor="ms")
    for sx in (W / 2 - tw / 2 - 58, W / 2 + tw / 2 + 58):
        d.line([sx - 26, 629, sx + 26, 629], fill=(110, 168, 230), width=2)

    # 版本
    f_ver = ImageFont.truetype(F_LATIN, 48)
    d.text((W / 2, 672), "V1.0", font=f_ver, fill=AMBER, anchor="mm")
    vw = d.textlength("V1.0", font=f_ver)
    for sx in (W / 2 - vw / 2 - 30, W / 2 + vw / 2 + 30):
        d.line([sx - 22, 672, sx + 22, 672], fill=(200, 150, 80), width=2)

    # 能力标签条
    f_cap = ImageFont.truetype(F_TEXT, 14)
    cap = "不预设世界观　·　创世系统　·　世界自运行"
    cw = d.textlength(cap, font=f_cap) + 30
    d.rounded_rectangle([W / 2 - cw / 2, 700, W / 2 + cw / 2, 728], radius=4,
                        fill=(12, 18, 32), outline=(96, 150, 210), width=1)
    d.text((W / 2, 714), cap, font=f_cap, fill=(196, 220, 250), anchor="mm")

    # 页脚
    f_foot = ImageFont.truetype(F_LATIN, 11)
    d.text((W / 2, 745), "S I L L Y T A V E R N   C H A R A C T E R   C A R D",
           font=f_foot, fill=(120, 142, 175), anchor="mm")

    im.save(COVER, "PNG")
    print("cover ->", COVER)

    # ---------- 打包 PNG 角色卡 ----------
    card = json.load(open(CARD_JSON, encoding="utf-8"))
    v3 = {"spec": "chara_card_v3", "spec_version": "3.0", "data": card["data"]}
    v2 = {"spec": "chara_card_v2", "spec_version": "2.0",
          "data": {k: card["data"][k] for k in card["data"] if k != "group_only_greetings"}}
    b64_v3 = base64.b64encode(json.dumps(v3, ensure_ascii=False).encode("utf-8"))
    b64_v2 = base64.b64encode(json.dumps(v2, ensure_ascii=False).encode("utf-8"))

    raw = open(COVER, "rb").read()
    assert raw[:8] == b"\x89PNG\r\n\x1a\n"

    def chunk(ctype, data):
        return (struct.pack(">I", len(data)) + ctype + data
                + struct.pack(">I", zlib.crc32(ctype + data) & 0xffffffff))

    out = bytearray(raw[:8])
    pos = 8
    inserted = False
    while pos < len(raw):
        ln = struct.unpack(">I", raw[pos:pos + 4])[0]
        ctype = raw[pos + 4:pos + 8]
        body = raw[pos:pos + 12 + ln]
        if not inserted and ctype == b"IDAT":
            out += chunk(b"tEXt", b"chara\x00" + b64_v2)
            out += chunk(b"tEXt", b"ccv3\x00" + b64_v3)
            inserted = True
        out += body
        pos += 12 + ln

    open(CARD_PNG, "wb").write(bytes(out))
    print("card  ->", CARD_PNG, len(out), "bytes")


if __name__ == "__main__":
    main()
