from flask import Flask, render_template, request
import os, json

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

inch = 72

addons = json.load(open('addons.json', 'rb'))
equipment = json.load(open('equipment.json', 'rb'))

from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib import colors

# Create a new stylesheet object
custom_styles = getSampleStyleSheet()

# Modify existing styles or add new ones
custom_styles.add(ParagraphStyle(
    name='TitleStyle',
    fontName='Courier',
    fontSize=24,
    leading=0,  # Line height
    alignment=0,  # Center alignment
    textColor=colors.black
))

custom_styles.add(ParagraphStyle(
    name='BodyStyle',
    fontName='Courier',
    fontSize=12,
    leading=0,
    alignment=0,  # Left alignment
    textColor=colors.black
))

highlight_color = colors.lightgreen

custom_styles.add(ParagraphStyle(
    name='HighlightStyle',
    fontName='Courier',
    fontSize=12,
    leading=0,
    alignment=0,  # Left alignment
    textColor=colors.black,
    borderColor=highlight_color
))


# Access styles like this:
title_style = custom_styles['TitleStyle']
body_style = custom_styles['BodyStyle']
highlight_style = custom_styles['BodyStyle']

def literal(x):
    if x > 0:
        return "+" + str(x)
    return str(x)

def split(line):
    max_len = 60
    final = ['']

    for token in line.split(' '):
        if token == "\n":
            final.append('')
            continue
        else:
            final[-1] += token + ' '
            if len(final[-1]) >= max_len:
                final.append('')

    return final

def cursed(obj):
    final = ""
    final += "\n".join(split(obj["description"][0]["content"]))
    try:
        if len(obj["description"]) > 1:
            for d in obj["description"][1]["subcontent"]:
                final += "\n    • " + d["content"] + "\n    " + "\n    ".join(split(d["subcontent"][0]["content"]))
    except KeyError:
        pass
    return final

def get_addon(a):
    for add in addons:
        if add['id'] == a:
            return add
        
    return None

def get_equipment(a):
    print(a)
    for add in equipment:
        if add['id'] == a:
            return add
        
    return equipment[0]

def generate_pdf_with_table(data):
    filename = f"{data['Name']}.pdf"
    doc = SimpleDocTemplate(filename, pagesize=letter)

    page_width, page_height = letter  # Default letter size (8.5 x 11 inches)
    
    content = []
    content.append(Paragraph(data["Name"], title_style))

    content.append(Spacer(page_width, inch * 0.5))

    table_style = TableStyle(
        [
            ('INNERGRID', (0,0), (-1,-1), 0.25, (0, 0, 0)),
            ('BOX', (0,0), (-1,-1), 0.25, (0, 0, 0)),
            ('FONTNAME', (0, 0), (-1, -1), "Courier")
        ]
    )
    
    table_style_2 = TableStyle(
        [
            ('FONTNAME', (0, 0), (-1, -1), "Courier")
        ]
    )

    # Data for the table
    table_data = [
        [ "Faction: " + str(data["Faction"]["Name"]) ] , [Table([[ "Ducats: " + str(data["DucatCost"]), "Glory: " + str(data["GloryCost"]) ]], colWidths=None, style=table_style)]
    ]

    # Create the table and apply a style
    table = Table(table_data, colWidths=None)
    table.setStyle(table_style)

    content.append(table)
    content.append(Spacer(page_width, inch * 0.5))

    for member in data["Members"]:
        try:
            model = member["Model"]
            obj = model["Object"]
            traits = "Traits: "

            for trait in obj["Tags"]:
                traits += trait["tag_name"].capitalize() + ", "
            
            traits = traits.removesuffix(', ')
        
            # Define the outer table's data
            outer_data = [
                [ member["Name"], traits ],
                [Table([[f"Base: {obj["Base"][0]}", f"Range: {literal(obj["Ranged"][0])}", f"Melee: {literal(obj["Melee"][0])}"]], colWidths=None, style=table_style), Table([[f"Move: {obj["Movement"][0]}\"", obj["Name"]]], colWidths=None, style=table_style)],
            ]

            weapon_data = [
                ['Weapons:'],
            ]
            
            for weapon in member["Equipment"]:
                weapon_obj = weapon["Object"]
                if weapon_obj["EquipType"]:
                    weapon_data.append([Table([["Name", "Type", "Range", "Keywords"], [weapon_obj["Name"], weapon_obj["EquipType"], weapon_obj["Range"], ", ".join([t["tag_name"] for t in weapon_obj["Tags"]])]], colWidths=None, style=table_style)])

                    if len(weapon_obj["Description"]):
                        weapon_data.append([Table([[f"Rules:\n{"\n".join(split(cursed(get_equipment(weapon_obj['ID']))))}"]], colWidths=None, style=table_style_2)])

            abilities_data = [
                ['Abilities/Upgrades:'],
            ]
            
            string = ""

            for ability in obj["Abilities"]:
                a = get_addon(ability["Content"])
                string += "\n• " + a["name"] + ":\n" + cursed(a)

            for upgrade in member["Upgrades"]:
                string += "\n• " + upgrade["Name"] + ":\n" + "\n".join(split(upgrade["Description"][0]["Content"]))

            abilities_data.append([Table([[string]], colWidths=None, style=table_style_2)])
            
            equipment_data = [
                ['Equipment:'],
            ]
            
            string = ""

            for equipment in member["Equipment"]:
                e = get_equipment(equipment['ID'])
                if len(e["description"]) and e["category"] == "equipment":
                    string += "\n• " + e["name"] + ":\n" + "\n".join(split(e["description"][0]["subcontent"][0]["content"]))

            equipment_data.append([Table([[string]], colWidths=None, style=table_style_2)])

            # Rebuild the outer table with the nested tables
            outer_table = Table(outer_data, colWidths=None, rowHeights=0.35*inch)    
            outer_table.setStyle(table_style)
            content.append(outer_table)
            if len(weapon_data) != 1:
                weapon_table = Table(weapon_data, colWidths=None)
                weapon_table.setStyle(table_style)
                content.append(weapon_table)
            if len(abilities_data) != 1:
                abilities_table = Table(abilities_data, colWidths=None)
                abilities_table.setStyle(table_style)
                content.append(abilities_table)
            if len(equipment_data) != 1:
                equipment_table = Table(equipment_data, colWidths=None)
                equipment_table.setStyle(table_style)
                content.append(equipment_table)
            content.append(Spacer(page_width, inch * 0.5))
        except IndexError:
            pass

    doc.build(content)
    
app = Flask(__name__)

app.config['ALLOWED_EXTENSIONS'] = {'json'}

# Check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def home():
    return render_template('index.html')

@app.route("/about")
def about():
    return render_template("about.html")

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        f = request.files.get('file_input')
        
        if f and allowed_file(f.filename):
            data = json.load(f)
            generate_pdf_with_table(data)
    
    return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True)