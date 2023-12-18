from PIL import Image, ImageFont, ImageDraw


TEXT_COORDINATES = [(633, 55),  # Имя
          (633, 120),  # Город
          (633, 215),  # Профессия
          (670, 482),  # Любимые предметы
          (1308, 445),  # Компетенции
          (30, 745),  # ВУЗ
          (30, 930),  # Специальность
          ]


def TeamCardsGenerator(db,
                       facilitatorId: int
                       ):
    db.execute("""SELECT name, city, profession,
               "favoriteSubjects", competencies, university,
               specialties FROM "Teams" WHERE "facilitatorId"=%s""",
               (str(facilitatorId),))
    info = list(db.fetchall()[0])

    img = Image.open("res/Images/origin.jpg")
    draw = ImageDraw.Draw(img)
    font_path = "res/Fonts/Golos-Text/golos-text_regular.ttf"

    font = ImageFont.truetype(font_path, 50)
    draw.text(TEXT_COORDINATES[0], info[0], (0, 0, 0), font=font)

    font = ImageFont.truetype(font_path, 38)
    draw.text(TEXT_COORDINATES[1], info[1], (0, 0, 0), font=font)

    font = ImageFont.truetype(font_path, 42)
    draw.text(TEXT_COORDINATES[2], " ".join(info[2].split()[:len(info[2].split()) // 2]) +\
              "\n" + " ".join(info[2].split()[len(info[2].split()) // 2:]),
              (0, 0, 0), font=font)

    font = ImageFont.truetype(font_path, 34)

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

    img.save(f'res/Images/TeamCards/{facilitatorId}.jpg')
