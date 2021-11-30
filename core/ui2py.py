import os

def convert_ui_to_py():
    """ Конвертирование .ui в .py """
    pyuic_main_command = "pyuic5 ../resources/main_app.ui -o interface_main_app.py"
    pyuic_research_command = "pyuic5 ../resources/research_app.ui -o interface_research_app.py"
    os.system(pyuic_main_command)
    os.system(pyuic_research_command)


if __name__ == "__main__":
    convert_ui_to_py()