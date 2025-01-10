from flask import Flask, render_template, request, send_file
import os, json, time

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet

inch = 72

addons = json.load(open(os.path.join('data', 'addons.json'), 'rb'))
equipment = json.load(open(os.path.join('data', 'equipment.json'), 'rb'))

from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib import colors

# Create a new stylesheet object
custom_styles = getSampleStyleSheet()

def literal(x):
    if x > 0:
        return "+" + str(x)
    return str(x)

def split(line):
    max_len = 60
    final = ['']

    for token in line.split(' '):
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

def cursed_weapon(obj):
    final = ""
    final += "\n".join(split(obj["Description"][0]["SubContent"][0]["Content"]))
    try:
        if len(obj["Description"][0]["SubContent"]) > 1:
            for d in obj["Description"][0]["SubContent"][1]["SubContent"]:
                final += "\n    • " + d["Content"]
    except KeyError:
        pass
    return final

def get_addon(a):
    for add in addons:
        if add['id'] == a:
            return add
        
    return None

def get_equipment(a):
    for add in equipment:
        if add['id'] == a:
            return add
        
    return equipment[0]

def generate_pdf_with_table(data, ignore_tough, corner_rounding, page_splitting, color):
    # Modify existing styles or add new ones
    try:
        custom_styles.add(ParagraphStyle(
            name='TitleStyle',
            fontName='Courier',
            fontSize=24,
            leading=0,  # Line height
            alignment=0,  # Center alignment
            textColor=color
        ))

        custom_styles.add(ParagraphStyle(
            name='BodyStyle',
            fontName='Courier',
            fontSize=12,
            leading=0,
            alignment=0,  # Left alignment
            textColor=colors.black
        ))
    except:
        pass

    # Access styles like this:
    title_style = custom_styles['TitleStyle']
    body_style = custom_styles['BodyStyle']
    highlight_style = custom_styles['BodyStyle']

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
            ('FONTNAME', (0, 0), (-1, -1), "Courier"),
            ('ROUNDEDCORNERS', [8 * corner_rounding] * 4)
        ]
    )

    table_style_3 = TableStyle(
        [
            ('INNERGRID', (0,0), (-1,-1), 0.25, (0, 0, 0)),
            ('BOX', (0,0), (-1,-1), 0.25, (0, 0, 0)),
            ('FONTNAME', (0, 0), (-1, -1), "Courier"),
            ('BACKGROUND', (0, 0), (-1, -1), color)
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
                [Table([[f"Base: {obj['Base'][0]}", f"Range: {literal(obj['Ranged'][0])}", f"Melee: {literal(obj['Melee'][0])}"]], colWidths=None, style=table_style), Table([[f"Move: {obj['Movement'][0]}\"", obj['Name']]], colWidths=None, style=table_style)],
            ]

            weapon_data = [
                ['Weapons:'],
            ]
            
            for weapon in member["Equipment"]:
                weapon_obj = weapon["Object"]
                if weapon_obj["EquipType"]:
                    weapon_data.append([
                        Table([
                            ["Name", "Type", "Range", "Keywords", "Modifiers"],
                            [weapon_obj["Name"],
                            weapon_obj["EquipType"],
                            weapon_obj["Range"],
                            ", ".join([t["tag_name"] for t in weapon_obj["Tags"]]),
                            weapon_obj["Modifiers"][0] if (weapon_obj["Modifiers"] and len(weapon_obj["Modifiers"])) else ""]
                    ], colWidths=None, style=table_style)]
                    )

                    if weapon_obj["Modifiers"] and len(weapon_obj["Modifiers"]):
                        weapon_data.append([Table([[f"Modifiers:\n{"\n".join(split(weapon_obj["Modifiers"][0]))}"]], colWidths=None, style=table_style_2)])

                    if len(weapon_obj["Description"]):
                        weapon_data.append([Table([[f"Rules:\n{cursed_weapon(weapon_obj)}"]], colWidths=None, style=table_style_2)])

            abilities_data = [
                ['Abilities/Upgrades:'],
            ]
            
            string = ""

            for ability in obj["Abilities"]:
                a = get_addon(ability["Content"])
                if a["name"] in ["Tough", "Strong", "Fear", "Infiltrator"] and ignore_tough:
                    continue
                string += "\n• " + a["name"] + ":\n" + cursed(a)

            for upgrade in member["Upgrades"]:
                string += "\n• " + upgrade["Name"] + ":\n" + "\n".join(split(upgrade["Description"][0]["Content"]))

            if string != "":
                if len(string.splitlines()) > 50:
                    line1 = "\n".join(string.splitlines()[:50])
                    line2 = "\n".join(string.splitlines()[50:])
                    abilities_data.append([Table([[line1]], colWidths=None, style=table_style_2)])
                    abilities_data.append([Table([[line2]], colWidths=None, style=table_style_2)])
                else:
                    abilities_data.append([Table([[string]], colWidths=None, style=table_style_2)])

            skills_data = [
                ['Skills/Injuries:'],
            ]
            
            string = ""

            for skill in member["Skills"]:
                string += "\n• " + skill["name"] + ":\n" + "\n".join(split(skill["description"][0]["content"]))

            for injury in member["Injuries"]:
                string += "\n• " + injury["Name"] + ":\n" + "\n".join(split(injury["Description"][0]["Content"]))

            if string != "":
                if len(string.splitlines()) > 50:
                    line1 = "\n".join(string.splitlines()[:50])
                    line2 = "\n".join(string.splitlines()[50:])
                    skills_data.append([Table([[line1]], colWidths=None, style=table_style_2)])
                    skills_data.append([Table([[line2]], colWidths=None, style=table_style_2)])
                else:
                    skills_data.append([Table([[string]], colWidths=None, style=table_style_2)])
            
            equipment_data = [
                ['Equipment:'],
            ]
            
            string = ""

            for equipment in member["Equipment"]:
                e = get_equipment(equipment['ID'])
                if len(e["description"]) and e["category"] == "equipment":
                    string += "\n• " + e["name"] + ":\n" + "\n".join(split(e["description"][0]["subcontent"][0]["content"]))

            if string != "":
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
            if len(skills_data) != 1:
                skills_table = Table(skills_data, colWidths=None)
                skills_table.setStyle(table_style)
                content.append(skills_table)
            if len(equipment_data) != 1:
                equipment_table = Table(equipment_data, colWidths=None)
                equipment_table.setStyle(table_style)
                content.append(equipment_table)
            if page_splitting:
                content.append(PageBreak())
            else:
                content.append(Spacer(page_width, inch * 0.5))
        except IndexError:
            pass

    doc.build(content)

    return doc.filename
    
app = Flask(__name__)

app.config['ALLOWED_EXTENSIONS'] = {'json'}

# Check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route("/about")
def about():
    return render_template("about.html")

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        f = request.files.get('file_input')
        ignore_tough = 'ignore_tough' in request.form.getlist('checkbox1')
        rounded_corners = 'rounded_corners' in request.form.getlist('checkbox2')
        page_splitting = 'page_splitting' in request.form.getlist('checkbox3')
        highlight_color = request.form.getlist("colorPicker")[0]
        
        if f and allowed_file(f.filename):
            data = json.load(f)
            name = generate_pdf_with_table(data, ignore_tough, rounded_corners, page_splitting, highlight_color)
    
            return send_file(name, mimetype="application/pdf", as_attachment=True)

    return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True)