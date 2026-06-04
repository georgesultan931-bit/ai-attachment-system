from pathlib import Path
from random import Random

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "static" / "images"
OUT.mkdir(parents=True, exist_ok=True)


def font(size, bold=False):
    candidates = [
        "segoeuib.ttf" if bold else "segoeui.ttf",
        "arialbd.ttf" if bold else "arial.ttf",
    ]

    for name in candidates:
        try:
            return ImageFont.truetype(name, size=size)
        except OSError:
            continue

    return ImageFont.load_default()


def rounded(draw, xy, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def shadow_card(base, xy, radius, fill, shadow=(15, 23, 42, 48), offset=(0, 16)):
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    layer_draw = ImageDraw.Draw(layer)
    sx1, sy1, sx2, sy2 = xy
    ox, oy = offset
    layer_draw.rounded_rectangle(
        (sx1 + ox, sy1 + oy, sx2 + ox, sy2 + oy),
        radius=radius,
        fill=shadow,
    )
    layer = layer.filter(ImageFilter.GaussianBlur(18))
    base.alpha_composite(layer)
    draw = ImageDraw.Draw(base)
    rounded(draw, xy, radius, fill)


def gradient(size, top, bottom):
    width, height = size
    image = Image.new("RGBA", size)
    pixels = image.load()

    for y in range(height):
        ratio = y / max(height - 1, 1)
        color = tuple(
            int(top[index] * (1 - ratio) + bottom[index] * ratio)
            for index in range(3)
        ) + (255,)
        for x in range(width):
            pixels[x, y] = color

    return image


def draw_avatar(draw, center, radius, fill, accent):
    x, y = center
    draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=fill)
    draw.ellipse((x - radius // 2, y - radius // 2 - 9, x + radius // 2, y + radius // 2 - 9), fill=(255, 255, 255, 235))
    draw.rounded_rectangle(
        (x - radius // 2 - 12, y + radius // 6, x + radius // 2 + 12, y + radius + 10),
        radius=radius // 2,
        fill=accent,
    )


def add_noise(image, amount=11, seed=7):
    rng = Random(seed)
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    pixels = overlay.load()

    for y in range(image.height):
        for x in range(image.width):
            value = rng.randint(0, amount)
            pixels[x, y] = (255, 255, 255, value)

    image.alpha_composite(overlay)
    return image


def hero_recruitment():
    img = gradient((1400, 920), (12, 30, 41), (20, 83, 91))
    img = add_noise(img, 9, 3)
    draw = ImageDraw.Draw(img)

    for box, fill in [
        ((860, 80, 1350, 470), (255, 255, 255, 28)),
        ((60, 580, 510, 875), (255, 255, 255, 24)),
        ((1090, 590, 1370, 870), (255, 183, 77, 32)),
    ]:
        rounded(draw, box, 42, fill)

    shadow_card(img, (105, 120, 740, 785), 44, (255, 255, 255, 244))
    draw = ImageDraw.Draw(img)
    draw.text((150, 170), "AI Matching Overview", fill=(15, 23, 42), font=font(42, True))
    draw.text((150, 230), "Matching, interviews and approvals in one calm workflow.", fill=(71, 85, 105), font=font(22))

    colors = [(14, 165, 233), (16, 185, 129), (245, 158, 11), (239, 68, 68)]
    labels = ["Skills", "CV", "Meet", "Offer"]

    for i, (color, label) in enumerate(zip(colors, labels)):
        x = 155 + i * 140
        rounded(draw, (x, 300, x + 110, 395), 24, color + (255,))
        draw.text((x + 24, 326), label, fill=(255, 255, 255), font=font(20, True))

    chart_x, chart_y = 150, 460
    for i, height in enumerate([160, 118, 205, 88, 175]):
        x = chart_x + i * 100
        rounded(draw, (x, chart_y + 230 - height, x + 54, chart_y + 230), 18, (20, 184, 166, 255))

    draw.line((150, 690, 655, 690), fill=(226, 232, 240), width=3)
    draw.line((150, 455, 150, 690), fill=(226, 232, 240), width=3)

    shadow_card(img, (770, 220, 1265, 780), 48, (248, 250, 252, 246))
    draw = ImageDraw.Draw(img)
    draw.text((825, 270), "Candidate Shortlist", fill=(15, 23, 42), font=font(36, True))

    avatar_colors = [(14, 165, 233), (245, 158, 11), (16, 185, 129)]
    for index in range(3):
        y = 360 + index * 125
        draw_avatar(draw, (860, y + 28), 36, avatar_colors[index] + (255,), (30, 41, 59, 255))
        draw.text((925, y), f"Candidate {index + 1}", fill=(15, 23, 42), font=font(26, True))
        draw.text((925, y + 36), "Strong skills match", fill=(100, 116, 139), font=font(20))
        rounded(draw, (1110, y + 14, 1215, y + 56), 21, (220, 252, 231, 255))
        draw.text((1132, y + 23), f"{92 - index * 8}%", fill=(22, 101, 52), font=font(20, True))

    img.convert("RGB").save(OUT / "home-platform-hero.png", quality=94)


def dashboard_visual(name, title, subtitle, top, bottom, icon_color):
    img = gradient((900, 520), top, bottom)
    img = add_noise(img, 8, 10)
    draw = ImageDraw.Draw(img)

    shadow_card(img, (55, 55, 845, 465), 36, (255, 255, 255, 242))
    draw = ImageDraw.Draw(img)
    draw.text((95, 95), title, fill=(15, 23, 42), font=font(34, True))
    draw.text((95, 142), subtitle, fill=(100, 116, 139), font=font(21))

    for i, label in enumerate(["Profile", "Skills", "Interviews"]):
        x = 95 + i * 215
        rounded(draw, (x, 205, x + 175, 305), 26, (248, 250, 252, 255))
        draw.ellipse((x + 22, 230, x + 66, 274), fill=icon_color + (255,))
        draw.text((x + 82, 226), label, fill=(15, 23, 42), font=font(20, True))
        draw.text((x + 82, 256), "Ready", fill=(100, 116, 139), font=font(17))

    points = [(110, 390), (230, 350), (350, 374), (470, 310), (590, 332), (710, 275), (805, 295)]
    draw.line(points, fill=icon_color + (255,), width=8, joint="curve")

    for point in points:
        x, y = point
        draw.ellipse((x - 10, y - 10, x + 10, y + 10), fill=(255, 255, 255), outline=icon_color + (255,), width=5)

    img.convert("RGB").save(OUT / name, quality=94)


hero_recruitment()
dashboard_visual(
    "student-dashboard-visual.png",
    "Student Progress",
    "Profile strength, opportunities and application movement.",
    (235, 249, 255),
    (221, 247, 235),
    (20, 184, 166),
)
dashboard_visual(
    "employer-dashboard-visual.png",
    "Employer Console",
    "Hiring pipeline, candidate quality and interviews.",
    (255, 247, 237),
    (229, 244, 255),
    (14, 165, 233),
)
dashboard_visual(
    "admin-dashboard-visual.png",
    "System Control",
    "Approvals, placements and platform health.",
    (240, 253, 244),
    (255, 247, 237),
    (245, 158, 11),
)

print(f"Generated visual assets in {OUT}")
