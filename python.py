
import os
import subprocess
import curses
import re  # Importar el módulo para usar expresiones regulares

def run_git_command(command, path, silent=False):
    """
    Ejecuta un comando de Git en el directorio especificado.
    Si silent=True, solo muestra errores críticos.
    """
    result = subprocess.run(f"cd {path} && {command}", shell=True, text=True, capture_output=True)
    if result.returncode != 0:
        print("Hubo un error al ejecutar el comando.")
        print(result.stderr)
        return None
    if not silent:
        print(result.stdout)
    return result.stdout.strip()


def get_commit_list(path):
    """
    Obtiene una lista de commits en formato reducido.
    """
    log = run_git_command("git log --oneline --decorate --all --no-color", path)
    if log:
        return log.splitlines()
    else:
        print("No se encontraron commits en el historial.")
        return []


def select_commit(stdscr, commit_list):
    """
    Permite al usuario seleccionar un commit de la lista usando las teclas de flecha.
    """
    curses.curs_set(0)  # Ocultar el cursor
    current_row = 0  # Empezar desde la primera línea

    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()

        # Mostrar la lista de commits
        for idx, commit in enumerate(commit_list):
            x = 0
            y = idx
            if idx == current_row:
                stdscr.addstr(y, x, commit, curses.A_REVERSE)
            else:
                stdscr.addstr(y, x, commit)

        stdscr.refresh()

        key = stdscr.getch()

        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1  # Desplazarse hacia arriba
        elif key == curses.KEY_DOWN and current_row < len(commit_list) - 1:
            current_row += 1  # Desplazarse hacia abajo
        elif key == 10:  # Enter
            return commit_list[current_row]  # Seleccionamos el commit actual


def check_and_add_remote(path):
    """
    Verifica si hay un repositorio remoto configurado y lo agrega si no existe.
    """
    print("\nVerificando si hay un remoto configurado...")
    result = subprocess.run(f"cd {path} && git remote show origin > NUL 2>&1", shell=True)
    if result.returncode != 0:
        print("No se encontró un repositorio remoto configurado.")
        url = input("Introduce la URL del repositorio remoto: ").strip()
        if url:
            run_git_command(f"git remote add origin {url}", path)
        else:
            print("No se proporcionó una URL. No se pudo configurar el remoto.")
            return False
    else:
        print("Repositorio remoto configurado correctamente.")
    return True


def reset_or_revert(command_type, path):
    """
    Permite realizar un reset o revert en base a un commit seleccionado de la lista.
    """
    commit_list = get_commit_list(path)

    # Usamos curses para seleccionar un commit
    if commit_list:
        selected_commit = curses.wrapper(select_commit, commit_list)
        if not selected_commit:
            print("No se seleccionó un commit. Operación cancelada.")
            return

        print(f"\nSe seleccionó el commit: {selected_commit}")

        # Extraemos el hash del commit asegurándonos de que esté limpio
        commit_hash = selected_commit.split(" ")[0].strip()  # Extraemos solo el hash del commit
        print(f"Hash del commit seleccionado: {commit_hash}")  # Debugging

        # Comando para reset o revert
        try:
            if command_type == "reset --hard":
                # Ejecutar el reset asegurándonos de no incluir rutas extrañas
                result = run_git_command(f"git reset --hard {commit_hash}", path)
                if result:
                    print(f"Reseteado correctamente al commit {commit_hash}")
            elif command_type == "revert":
                # Solicitar mensaje personalizado para el revert
                revert_message = input("\nIntroduce el mensaje para el revert: ").strip()
                if not revert_message:
                    print("No se proporcionó un mensaje. Operación cancelada.")
                    return

                # Ejecutamos el comando de revert con el mensaje
                result = run_git_command(f"git revert {commit_hash} -m \"{revert_message}\"", path)
                if result:
                    print(f"Revertido correctamente al commit {commit_hash}")
        except Exception as e:
            print(f"Error al ejecutar {command_type}: {str(e)}")
            return

        # Confirmar si se desean subir los cambios al repositorio remoto
        decision = input("\n¿Deseas subir los cambios al repositorio remoto? (s para sí, Enter para no): ").strip().lower()
        if decision == 's':
            if check_and_add_remote(path):
                branch_name = run_git_command("git rev-parse --abbrev-ref HEAD", path)
                if branch_name:
                    try:
                        push_command = (
                            f"git push origin {branch_name} --force" if command_type == "reset --hard" else f"git push origin {branch_name}"
                        )
                        run_git_command(push_command, path)
                        print("Cambios subidos exitosamente.")
                    except Exception as e:
                        print(f"Error al intentar subir cambios: {str(e)}")


def create_new_branch(path):
    """
    Crea una nueva rama y la sube al remoto.
    """
    branch_name = input("Introduce el nombre de la nueva rama: ").strip()
    if not branch_name:
        print("No se proporcionó un nombre de rama. Operación cancelada.")
        return

    try:
        run_git_command(f"git checkout -b {branch_name}", path)
        print(f"Se creó y se cambió a la nueva rama '{branch_name}'.")

        if check_and_add_remote(path):
            run_git_command(f"git push -u origin {branch_name}", path)
            print(f"Rama '{branch_name}' subida al remoto correctamente.")
    except Exception as e:
        print(f"Error al crear o subir la nueva rama: {str(e)}")


def select_branch(stdscr, branch_list):
    """
    Permite al usuario seleccionar una rama de la lista usando las teclas de flecha.
    """
    curses.curs_set(0)  # Ocultar el cursor
    current_row = 0  # Empezar desde la primera línea

    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()

        # Mostrar la lista de ramas
        for idx, branch in enumerate(branch_list):
            x = 0
            y = idx
            if idx == current_row:
                stdscr.addstr(y, x, branch, curses.A_REVERSE)
            else:
                stdscr.addstr(y, x, branch)

        stdscr.refresh()

        key = stdscr.getch()

        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1  # Desplazarse hacia arriba
        elif key == curses.KEY_DOWN and current_row < len(branch_list) - 1:
            current_row += 1  # Desplazarse hacia abajo
        elif key == 10:  # Enter
            return branch_list[current_row]  # Seleccionamos la rama actual


def commit_and_push(path):
    """
    Realiza un commit y push al repositorio remoto.
    """
    mensaje = input("Introduce el mensaje del commit: ")

    result = run_git_command("git status --porcelain", path)
    if not result:
        print("No hay cambios para hacer commit.")
        return

    run_git_command("git add .", path)
    run_git_command(f"git commit -m \"{mensaje}\"", path)

    if check_and_add_remote(path):
        print("\nRealizando 'git pull' con rebase para evitar el error de 'non-fast-forward'...")
        run_git_command("git pull --rebase origin master", path)

        decision = input("\n¿Deseas subir los cambios al repositorio remoto? (s para sí, Enter para no): ").strip().lower()
        if decision == 's':
            branch_name = run_git_command("git rev-parse --abbrev-ref HEAD", path)
            if branch_name:
                print(f"\nSubiendo cambios a la rama '{branch_name}' en el repositorio remoto...")
                run_git_command(f"git push -u origin {branch_name}", path)
        else:
            print("No se realizó el push. Cambios solo guardados localmente.")


def change_commit_message(path):
    """
    Cambia el mensaje de un commit reciente.
    """
    commit_list = get_commit_list(path)
    if not commit_list:
        print("No se encontró ningún commit.")
        return

    selected_commit = curses.wrapper(select_commit, commit_list)
    if not selected_commit:
        print("Operación cancelada.")
        return

    commit_hash = selected_commit.split()[0]
    new_message = input("Introduce el nuevo mensaje para el commit: ")
    if not new_message:
        print("No se proporcionó un mensaje. Operación cancelada.")
        return

    run_git_command(f"git commit --amend --no-edit -m \"{new_message}\"", path)
    print("Mensaje de commit actualizado correctamente.")

def initialize_or_clone_repo(path):
    """
    Inicializa un nuevo repositorio o clona uno existente, sobrescribiendo el directorio si es necesario.
    """
    # Asegúrate de que el directorio exista, sino, lo crea
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)

    print("\n=== Configuración Inicial de Git ===")
    print("1. Inicializar un nuevo repositorio (git init)")
    print("2. Clonar un repositorio existente (git clone)")
    print("3. Continuar sin inicializar/clonar")

    opcion = input("\nSelecciona una opción: ")

    if opcion == "1":
        run_git_command("git init", path)
    elif opcion == "2":
        url = input("Introduce la URL del repositorio a clonar: ")

        # Verifica si el directorio ya existe y contiene algo
        if os.path.exists(path) and os.listdir(path):
            print(f"El directorio {path} no está vacío.")
            print("Sobrescribiendo el contenido del directorio...")
            
            # Limpiar el directorio antes de clonar
            for filename in os.listdir(path):
                file_path = os.path.join(path, filename)
                try:
                    if os.path.isdir(file_path):
                        os.rmdir(file_path)  # Eliminar directorios vacíos
                    else:
                        os.remove(file_path)  # Eliminar archivos
                except Exception as e:
                    print(f"Error al eliminar {file_path}: {e}")

        # Aseguramos que el directorio esté vacío antes de clonar
        os.chdir(path)
        print(f"Ejecutando el comando: git clone {url} . en {path}")
        result = subprocess.run(f"git clone {url} .", shell=True, text=True, capture_output=True)
        if result.returncode == 0:
            print(f"Repositorio clonado correctamente en {path}")
        else:
            print(f"Error al clonar el repositorio: {result.stderr}")
    elif opcion == "3":
        print("Continuando sin inicializar ni clonar.")
    else:
        print("Opción no válida. Por favor, selecciona 1, 2 o 3.")
        initialize_or_clone_repo(path)

def main():
    """
    Menú principal del asistente de Git.
    """
    print("Bienvenido al asistente de Git")
    path = input("Introduce la ruta donde se encuentra el repositorio o se desea crear uno: ").strip()
    initialize_or_clone_repo(path)

    while True:
        print("\nOpciones:")
        print("1. Realizar un commit y push")
        print("2. Resetear a un commit específico")
        print("3. Revertir un commit")
        print("4. Cambiar mensaje commit")
        print("5. Crear nueva rama y subirla al remoto")
        print("6. Cambiar de rama")
        print("7. Subir los cambios al remoto")
        print("0. Salir")

        choice = input("\nSelecciona una opción: ").strip()

        if choice == "1":
            commit_and_push(path)
        elif choice == "2":
            reset_or_revert("reset --hard", path)
        elif choice == "3":
            reset_or_revert("revert", path)
        elif choice == "4":
            change_commit_message(path)
        elif choice == "5":
            create_new_branch(path)
        elif choice == "6":
            # Seleccionar la rama
            branches = run_git_command("git branch", path)
            if branches:
                branch_list = branches.splitlines()
                selected_branch = curses.wrapper(select_branch, branch_list)
                if selected_branch:
                    run_git_command(f"git checkout {selected_branch}", path)
                    print(f"Cambiado a la rama '{selected_branch}'")
        elif choice == "7":
            # Subir cambios al remoto
            commit_and_push(path)
        elif choice == "0":
            print("Saliendo...")
            break
        else:
            print("Opción no válida. Inténtalo de nuevo.")


if __name__ == "__main__":
    main()
