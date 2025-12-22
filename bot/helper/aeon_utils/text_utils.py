import re

FONTS = {
    "bold": {
        "a": "𝐚", "b": "𝐛", "c": "𝐜", "d": "𝐝", "e": "𝐞", "f": "𝐟", "g": "𝐠", "h": "𝐡", "i": "𝐢", "j": "𝐣", "k": "𝐤", "l": "𝐥", "m": "𝐦", "n": "𝐧", "o": "𝐨", "p": "𝐩", "q": "𝐪", "r": "𝐫", "s": "𝐬", "t": "𝐭", "u": "𝐮", "v": "𝐯", "w": "𝐰", "x": "𝐱", "y": "𝐲", "z": "𝐳",
        "A": "𝐀", "B": "𝐁", "C": "𝐂", "D": "𝐃", "E": "𝐄", "F": "𝐅", "G": "𝐆", "H": "𝐇", "I": "𝐈", "J": "𝐉", "K": "𝐊", "L": "𝐋", "M": "𝐌", "N": "𝐍", "O": "𝐎", "P": "𝐏", "Q": "𝐐", "R": "𝐑", "S": "𝐒", "T": "𝐓", "U": "𝐔", "V": "𝐕", "W": "𝐖", "X": "𝐗", "Y": "𝐘", "Z": "𝐙",
        "0": "𝟎", "1": "𝟏", "2": "𝟐", "3": "𝟑", "4": "𝟒", "5": "𝟓", "6": "𝟔", "7": "𝟕", "8": "𝟖", "9": "𝟗"
    },
    "italic": {
        "a": "𝘢", "b": "𝘣", "c": "𝘤", "d": "𝘥", "e": "𝘦", "f": "𝘧", "g": "𝘨", "h": "𝘩", "i": "𝘪", "j": "𝘫", "k": "𝘬", "l": "𝘭", "m": "𝘮", "n": "𝘯", "o": "𝘰", "p": "𝘱", "q": "𝘲", "r": "𝘳", "s": "𝘴", "t": "𝘵", "u": "𝘶", "v": "𝘷", "w": "𝘸", "x": "𝘹", "y": "𝘺", "z": "𝘻",
        "A": "𝘈", "B": "𝘉", "C": "𝘊", "D": "𝘋", "E": "𝘌", "F": "𝘍", "G": "𝘎", "H": "𝘏", "I": "𝘐", "J": "𝘑", "K": "𝘒", "L": "𝘓", "M": "𝘔", "N": "𝘕", "O": "𝘖", "P": "𝘗", "Q": "𝘘", "R": "𝘙", "S": "𝘚", "T": "𝘛", "U": "𝘜", "V": "𝘝", "W": "𝘞", "X": "𝘟", "Y": "𝘠", "Z": "𝘡",
        "0": "0", "1": "1", "2": "2", "3": "3", "4": "4", "5": "5", "6": "6", "7": "7", "8": "8", "9": "9"
    },
    "code": {
        "a": "𝚊", "b": "𝚋", "c": "𝚌", "d": "𝚍", "e": "𝚎", "f": "𝚏", "g": "𝚐", "h": "𝚑", "i": "𝚒", "j": "𝚓", "k": "𝚔", "l": "𝚕", "m": "𝚖", "n": "𝚗", "o": "𝚘", "p": "𝚙", "q": "𝚚", "r": "𝚛", "s": "𝚜", "t": "𝚝", "u": "𝚞", "v": "𝚟", "w": "𝚠", "x": "𝚡", "y": "𝚢", "z": "𝚣",
        "A": "𝙰", "B": "𝙱", "C": "𝙲", "D": "𝙳", "E": "𝙴", "F": "𝙵", "G": "𝙶", "H": "𝙷", "I": "𝙸", "J": "𝙹", "K": "𝙺", "L": "𝙻", "M": "𝙼", "N": "𝙽", "O": "𝙾", "P": "𝙿", "Q": "𝚀", "R": "𝚁", "S": "𝚂", "T": "𝚃", "U": "𝚄", "V": "𝚅", "W": "𝚆", "X": "𝚇", "Y": "𝚈", "Z": "𝚉",
        "0": "𝟶", "1": "𝟷", "2": "𝟸", "3": "𝟹", "4": "𝟺", "5": "𝟻", "6": "𝟼", "7": "𝟽", "8": "𝟾", "9": "𝟿"
    },
     "underline": {
        "a": "a_̲", "b": "b_̲", "c": "c_̲", "d": "d_̲", "e": "e_̲", "f": "f_̲", "g": "g_̲", "h": "h_̲", "i": "i_̲", "j": "j_̲", "k": "k_̲", "l": "l_̲", "m": "m_̲", "n": "n_̲", "o": "o_̲", "p": "p_̲", "q": "q_̲", "r": "r_̲", "s": "s_̲", "t": "t_̲", "u": "u_̲", "v": "v_̲", "w": "w_̲", "x": "x_̲", "y": "y_̲", "z": "z_̲",
        "A": "A_̲", "B": "B_̲", "C": "C_̲", "D": "D_̲", "E": "E_̲", "F": "F_̲", "G": "G_̲", "H": "H_̲", "I": "I_̲", "J": "J_̲", "K": "K_̲", "L": "L_̲", "M": "M_̲", "N": "N_̲", "O": "O_̲", "P": "P_̲", "Q": "Q_̲", "R": "R_̲", "S": "S_̲", "T": "T_̲", "U": "U_̲", "V": "V_̲", "W": "W_̲", "X": "X_̲", "Y": "Y_̲", "Z": "Z_̲",
        "0": "0", "1": "1", "2": "2", "3": "3", "4": "4", "5": "5", "6": "6", "7": "7", "8": "8", "9": "9"
    },
}

def apply_font(text, font_name):
    if not font_name:
        return text
    font_name = font_name.lower()
    if font_name not in FONTS:
        return text
    
    mapping = FONTS[font_name]
    
    # Split text by HTML tags, capturing the tags to keep them
    parts = re.split(r'(<[^>]+>)', text)
    result = []
    
    for part in parts:
        # If part is an HTML tag, keep it as is
        if part.startswith('<') and part.endswith('>'):
            result.append(part)
        else:
            # Apply font mapping to non-tag text
            transformed = ""
            for char in part:
                transformed += mapping.get(char, char)
            result.append(transformed)
            
    return "".join(result)

def clean_filename(name):
    # Remove special characters, keep alphanumeric, dots, hyphens, spaces, underscores
    # Logic: Replace anything NOT in allowed set with empty string
    return re.sub(r'[^\w\s\.-]', '', name)

def replace_filename(name, replace_text):
    if not replace_text:
        return name
    
    # replace_text format: "old:new | word:"
    # Split by |
    replacements = replace_text.split("|")
    for item in replacements:
        if ":" in item:
            old, new = item.split(":", 1)
            name = name.replace(old.strip(), new.strip())
        else:
             # Just a word to remove
             name = name.replace(item.strip(), "")
    return name
