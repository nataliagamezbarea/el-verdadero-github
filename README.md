# Instrucciones para ejecutar y crear un ejecutable de `github-commands.py`

## Pasos para ejecutar el script

1. **Instalar Python**  
   Asegúrate de tener instalado Python en tu sistema. Puedes descargarlo desde [python.org](https://www.python.org/).

2. **Clonar el repositorio**  
   Clona el repositorio desde GitHub utilizando el siguiente comando:
   ```bash
   git clone https://github.com/nataliagamezbarea/el-verdadero-github.git

3. **Acceder a la carpeta**  
   ```bash
    cd el-verdadero-github

4. **Dependencias**  
   ```bash
   pip install windows-curses

5. **Ejecutar python**  
   ```bash
    python  github-commands.py

6. **Crear ejecutable**  
   ```bash   
    pip install pyinstaller
   ```
      ```
    pyinstaller --onefile github-commands.py

