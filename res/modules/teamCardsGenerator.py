from PIL import Image, ImageFont, ImageDraw
import sqlite3


TEXT_COORDINATES = [(633, 55),  # Имя
          (633, 120),  # Город
          (633, 215),  # Профессия
          (670, 482),  # Любимые предметы
          (1308, 445),  # Компетенции
          (30, 745),  # ВУЗ
          (30, 930),  # Специальность
          ]


def TeamCardsGenerator(db: sqlite3.Cursor,
                       facilitatorId: int
                       ):
    info = list(db.execute("""SELECT name, city, profession,
                      favoriteSubjects, competencies, university, 
                      specialties FROM Teams WHERE facilitatorId=?""",
                                             (facilitatorId,)).fetchall()[0])

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
        if i != 3:
            if i == 4:
                text = ""
                comps = info[i].split(", ")
                for c in comps:
                    text += " ".join(c.split()[:len(c.split()) // 2]) +\
                        "\n" + " ".join(c.split()[len(c.split()) // 2:]) + "\n"
            else:
                text = " ".join(info[i].split()[:len(info[i].split()) // 2]) +\
                    "\n" + " ".join(info[i].split()[len(info[i].split()) // 2:])
        else:
            text = "\n".join(info[3].split(", "))

        draw.text(TEXT_COORDINATES[i], text, (255, 255, 255), font=font)

    img.save(f'./res/data/Images/TeamCards/{facilitatorId}.jpg')
