from PIL import Image, ImageFont, ImageDraw
import sqlite3


TEXT_COORDINATES = [(340, 41),  # Имя
          (340, 106),  # Город
          (340, 215),  # Профессия
          (30, 435),  # Хобби
          (575, 462),  # Любимые предметы
          (1210, 434),  # Компетенции
          (30, 716),  # ВУЗ
          (30, 902),  # Специальность
          ]


def TeamCardsGenerator(db: sqlite3.Cursor,
                       facilitatorId: int
                       ):
    info = list(db.execute("""SELECT name, city, profession, hobby,
                      favoriteSubjects, competencies, university, 
                      specialties FROM Teams WHERE facilitatorId=?""",
                                             (facilitatorId,)).fetchall()[0])

    info[3] = "\n".join(info[3].split(", "))
    info[4] = "\n".join(info[4].split(", "))
    info[5] = "\n".join(info[5].split(", "))

    info[6] = " ".join(info[6].split()[:len(info[6].split()) // 2]) + "\n" + " ".join(info[6].split()[len(info[6].split()) // 2:])
    info[7] = " ".join(info[7].split()[:len(info[7].split()) // 2]) + "\n" + " ".join(info[7].split()[len(info[7].split()) // 2:])

    img = Image.open("./res/data/Images/origin.jpg")
    draw = ImageDraw.Draw(img)

    font = ImageFont.truetype("./res/data/Fonts/Golos-Text/golos-text_regular.ttf", 50)
    draw.text(TEXT_COORDINATES[0], info[0], (0, 0, 0), font=font)

    font = ImageFont.truetype("./res/data/Fonts/Golos-Text/golos-text_regular.ttf", 38)
    draw.text(TEXT_COORDINATES[1], info[1], (0, 0, 0), font=font)

    font = ImageFont.truetype("./res/data/Fonts/Golos-Text/golos-text_regular.ttf", 42)
    draw.text(TEXT_COORDINATES[2], info[2], (0, 0, 0), font=font)

    font = ImageFont.truetype("./res/data/Fonts/Golos-Text/golos-text_regular.ttf", 34)

    for i in range(3, len(info)):
        draw.text(TEXT_COORDINATES[i], info[i], (255, 255, 255), font=font)

    img.save(f'./res/data/Images/TeamCards/{facilitatorId}.jpg')
