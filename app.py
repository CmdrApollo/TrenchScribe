# Trench Scribe v0.2.4

# imports
from flask import Flask, render_template, request, send_file
import os, json

from typing import Any

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet

inch = 72

# json data for description/equipment descriptions
addons = json.load(open(os.path.join('data', 'addons.json'), 'rb'))
equipment = json.load(open(os.path.join('data', 'equipment.json'), 'rb'))

# reportlab is used to actually generate the pdf files
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib import colors

# puts a '+' in front of positive integers
def literal(x: int) -> str:
    if x > 0:
        return "+" + str(x)
    return str(x)

# splits a single string into lines of ~60 chars
def split(line: str) -> list[str]:
    max_len = 60
    final = ['']

    for token in line.split(' '):
        final[-1] += token + ' '
        if len(final[-1]) >= max_len:
            final.append('')

    return final

# i don't even know how to describe this
# it extracts data from certain objects
# i made this function so that bulleted
# lists would work properly
def cursed(obj: dict[Any: Any]):
    final = ""
    final += "\n".join(split(obj["description"][0]["content"]))
    try:
        if len(obj["description"]) > 1:
            for d in obj["description"][1]["subcontent"]:
                final += "\n    • " + d["content"] + "\n    " + "\n    ".join(split(d["subcontent"][0]["content"]))
    except KeyError:
        pass
    return final

# pretty much same as cursed but made to
# work with weapons
def cursed_weapon(obj: dict[Any: Any]):
    final = ""
    final += "\n".join(split(obj["Description"][0]["SubContent"][0]["Content"]))
    try:
        if len(obj["Description"][0]["SubContent"]) > 1:
            for d in obj["Description"][0]["SubContent"][1]["SubContent"]:
                final += "\n    • " + d["Content"]
    except KeyError:
        pass
    return final

# searches the json data for a specific 'addon'/upgrade
def get_addon(a):
    for add in addons:
        if add['id'] == a:
            return add
        
    return addons[0]

# searches the json data for a specific piece of equipment
def get_equipment(a):
    for add in equipment:
        if add['id'] == a:
            return add
        
    return equipment[0]

def generate_pdf_with_table(data, ignore_tough, corner_rounding, page_splitting, color):
    # stylesheet object
    custom_styles = getSampleStyleSheet()

    # modify the custom stylesheet
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

    # access styles with these variables
    title_style = custom_styles['TitleStyle']
    body_style = custom_styles['BodyStyle']
    highlight_style = custom_styles['BodyStyle']

    # generate a doc name based on the warband name
    filename = f"{data['Name']}.pdf"
    # make the doc with reportlab
    doc = SimpleDocTemplate(filename, pagesize=letter)

    # store the letter page width and height to variables
    page_width, page_height = letter  # Default letter size (8.5 x 11 inches)
    
    # the contents of the document
    content = []
    # warband name as a title
    content.append(Paragraph(data["Name"], title_style))

    # spacer
    content.append(Spacer(page_width, inch * 0.5))
    content.append(HRFlowable(width="100%", thickness=1, lineCap='round', color='#808080', spaceBefore=1, spaceAfter=1, hAlign='CENTER', vAlign='BOTTOM', dash=None))
    content.append(Spacer(page_width, inch * 0.5))

    # main table style
    table_style = TableStyle(
        [
            ('INNERGRID', (0,0), (-1,-1), 0.25, (0, 0, 0)),
            ('BOX', (0,0), (-1,-1), 0.25, (0, 0, 0)),
            ('FONTNAME', (0, 0), (-1, -1), "Courier"),
            ('ROUNDEDCORNERS', [8 * corner_rounding] * 4)
        ]
    )
    
    # secondary table style
    table_style_2 = TableStyle(
        [
            ('FONTNAME', (0, 0), (-1, -1), "Courier")
        ]
    )

    # data for the overarching table
    table_data = [
        [ "Faction: " + str(data["Faction"]["Name"]) ] , [Table([[ "Ducats: " + str(data["DucatCost"]), "Glory: " + str(data["GloryCost"]) ]], colWidths=None, style=table_style)]
    ]

    # create the table and apply a style
    table = Table(table_data, colWidths=None)
    table.setStyle(table_style)

    # add the table to the content
    content.append(table)
    # spacer
    content.append(Spacer(page_width, inch * 0.5))

    for member in data["Members"]:
        try:
            # some widely-used dictionary objects
            model = member["Model"]
            obj = model["Object"]
            
            # add all traits from the model
            traits = "Traits: "

            for trait in obj["Tags"]:
                traits += trait["tag_name"].capitalize() + ", "
            
            traits = traits.removesuffix(', ')
        
            # define the model's outer table data
            outer_data = [
                [ member["Name"], traits ],
                [Table([[f"Base: {obj['Base'][0]}", f"Range: {literal(obj['Ranged'][0])}", f"Melee: {literal(obj['Melee'][0])}"]], colWidths=None, style=table_style), Table([[f"Move: {obj['Movement'][0]}\"", obj['Name']]], colWidths=None, style=table_style)],
            ]

            # define the model's weapon table data
            weapon_data = [
                ['Weapons:'],
            ]
            
            # populate the model's weapons
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

                    if len(weapon_obj["Description"]):
                        weapon_data.append([Table([[f"Rules:\n{cursed_weapon(weapon_obj)}"]], colWidths=None, style=table_style_2)])

            # define the model's abilities table data
            abilities_data = [
                ['Abilities/Upgrades:'],
            ]

            # populate the abilities and upgrades            
            string = ""

            for ability in obj["Abilities"]:
                a = get_addon(ability["Content"])
                if a["name"] in ["Tough", "Strong", "Fear", "Infiltrator", " Unholy Horror", "Demonic Horror", "Terrifying"] and ignore_tough:
                    continue
                string += "\n• " + a["name"] + ":\n" + cursed(a)

            for upgrade in member["Upgrades"]:
                string += "\n• " + upgrade["Name"] + ":\n" + "\n".join(split(upgrade["Description"][0]["Content"]))

            # split a string that's too long into two
            # will crash otherwise
            if string != "":
                if len(string.splitlines()) > 50:
                    line1 = "\n".join(string.splitlines()[:50])
                    line2 = "\n".join(string.splitlines()[50:])
                    abilities_data.append([Table([[line1]], colWidths=None, style=table_style_2)])
                    abilities_data.append([Table([[line2]], colWidths=None, style=table_style_2)])
                else:
                    abilities_data.append([Table([[string]], colWidths=None, style=table_style_2)])

            # define the model's skills table data
            skills_data = [
                ['Skills/Injuries:'],
            ]

            # populate the skills and injuries
            string = ""

            for skill in member["Skills"]:
                string += "\n• " + skill["name"] + ":\n" + "\n".join(split(skill["description"][0]["content"]))

            for injury in member["Injuries"]:
                string += "\n• " + injury["Name"] + ":\n" + "\n".join(split(injury["Description"][0]["Content"]))

            # split a string that's too long into two
            # will crash otherwise
            if string != "":
                if len(string.splitlines()) > 50:
                    line1 = "\n".join(string.splitlines()[:50])
                    line2 = "\n".join(string.splitlines()[50:])
                    skills_data.append([Table([[line1]], colWidths=None, style=table_style_2)])
                    skills_data.append([Table([[line2]], colWidths=None, style=table_style_2)])
                else:
                    skills_data.append([Table([[string]], colWidths=None, style=table_style_2)])
            
            # define the model's equipment table data
            equipment_data = [
                ['Equipment:'],
            ]

            # populate the equipment
            string = ""

            for equipment in member["Equipment"]:
                e = get_equipment(equipment['ID'])
                if len(e["description"]) and e["category"] in ["equipment", "armour"]:
                    string += "\n• " + e["name"] + ":\n" + "\n".join(split(e["description"][0]["subcontent"][0]["content"]))

            if string != "":
                equipment_data.append([Table([[string]], colWidths=None, style=table_style_2)])

            # build the outer table
            outer_table = Table(outer_data, colWidths=None, rowHeights=0.35*inch)    
            outer_table.setStyle(table_style)
            content.append(outer_table)
            
            # build weapon table and add it to content if not empty
            if len(weapon_data) != 1:
                weapon_table = Table(weapon_data, colWidths=None)
                weapon_table.setStyle(table_style)
                content.append(weapon_table)
            
            # build ability table and add it to content if not empty
            if len(abilities_data) != 1:
                abilities_table = Table(abilities_data, colWidths=None)
                abilities_table.setStyle(table_style)
                content.append(abilities_table)
            
            # build skill table and add it to content if not empty
            if len(skills_data) != 1:
                skills_table = Table(skills_data, colWidths=None)
                skills_table.setStyle(table_style)
                content.append(skills_table)
            
            # build equipment table and add it to content if not empty
            if len(equipment_data) != 1:
                equipment_table = Table(equipment_data, colWidths=None)
                equipment_table.setStyle(table_style)
                content.append(equipment_table)
            
            # split models based on page_splitting flag
            if page_splitting:
                content.append(PageBreak())
            else:
                content.append(Spacer(page_width, inch * 0.5))
                content.append(HRFlowable(width="100%", thickness=1, lineCap='round', color='#808080', spaceBefore=1, spaceAfter=1, hAlign='CENTER', vAlign='BOTTOM', dash=None))
                content.append(Spacer(page_width, inch * 0.5))
        except IndexError:
            pass

    # build the document
    doc.build(content)

    # return the filename of the document so
    # that flask can download it for the user
    return doc.filename

# make the app object and configure it
app = Flask(__name__)
app.config['ALLOWED_EXTENSIONS'] = {'json'}

# check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# about page
@app.route("/about")
def about():
    return render_template("about.html")

filename = ""

# home page
@app.route('/', methods=['GET', 'POST'])
def upload_file():
    global filename

    if len(filename):
        os.remove(filename)
        filename = ""

    if request.method == 'POST':
        # filename
        f = request.files.get('file_input')

        # flags
        ignore_tough = 'ignore_tough' in request.form.getlist('checkbox1')
        rounded_corners = 'rounded_corners' in request.form.getlist('checkbox2')
        page_splitting = 'page_splitting' in request.form.getlist('checkbox3')
        
        # warband color
        highlight_color = request.form.getlist("colorPicker")[0]
        
        if f and allowed_file(f.filename):
            # load the json and generate the data
            data = json.load(f)
            filename = generate_pdf_with_table(data, ignore_tough, rounded_corners, page_splitting, highlight_color)
    
            # download the file on the user's machine
            s = send_file(filename, mimetype="application/pdf", as_attachment=True)

            return s

    # render the home page html
    return render_template('index.html')

# run the app
if __name__ == "__main__":
    app.run(debug=True)
