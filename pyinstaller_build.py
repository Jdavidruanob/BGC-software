from PyInstaller.__main__ import run

run([
    "--noconfirm",
    "--onefile",
    "--windowed",
    "--add-data=assets;assets",
    "--add-data=styles;styles",
    "--collect-all=dateutil",
    "--collect-all=openpyxl",
    "--icon=app_icon2.ico",
    "--name=BGC-software",
    "app.py",
])
