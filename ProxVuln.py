import os
import re

def print_proxvuln_title():
    title = """
   
██████╗░██████╗░░█████╗░██╗░░██╗██╗░░░██╗██╗░░░██╗██╗░░░░░███╗░░██╗
██╔══██╗██╔══██╗██╔══██╗╚██╗██╔╝██║░░░██║██║░░░██║██║░░░░░████╗░██║
██████╔╝██████╔╝██║░░██║░╚███╔╝░╚██╗░██╔╝██║░░░██║██║░░░░░██╔██╗██║
██╔═══╝░██╔══██╗██║░░██║░██╔██╗░░╚████╔╝░██║░░░██║██║░░░░░██║╚████║
██║░░░░░██║░░██║╚█████╔╝██╔╝╚██╗░░╚██╔╝░░╚██████╔╝███████╗██║░╚███║
╚═╝░░░░░╚═╝░░╚═╝░╚════╝░╚═╝░░╚═╝░░░╚═╝░░░░╚═════╝░╚══════╝╚═╝░░╚══╝
    By: @Lup1n_3

    """
    print(title)

def sanitize_vm_name(name):
    # Reemplaza caracteres no permitidos con guiones
    sanitized_name = re.sub(r'[^a-zA-Z0-9.-]', '-', name)
    return sanitized_name

def list_ova_files():
    ova_files = [f for f in os.listdir() if f.endswith('.ova')]
    return ova_files

def list_vmdk_files():
    vmdk_files = [f for f in os.listdir() if f.endswith('.vmdk')]
    return vmdk_files

def download_ova_from_vulnhub():
    url = input("Introduce el enlace para descargar el archivo .ova desde VulnHub: ")
    filename = url.split('/')[-1]
    print(f"Descargando {filename} desde VulnHub...")
    os.system(f"wget {url}")
    print("\nDescarga completada.")

def convert_and_create_vm_from_vmdk(vmdk_file, vm_id):
    vm_name = os.path.splitext(os.path.basename(vmdk_file))[0]
    vm_name = sanitize_vm_name(vm_name)  # Sanitize the VM name
    vmdk_path = os.path.abspath(vmdk_file)  # Get the absolute path
    raw_path = os.path.abspath(f"{vm_name}.raw")  # Get the absolute path for the raw file

    print(f"Convirtiendo el disco {vmdk_file} a un formato aceptado por Proxmox...")
    os.system(f"qemu-img convert -O raw \"{vmdk_path}\" \"{raw_path}\"")

    print(f"Creando la máquina virtual en Proxmox (ID: {vm_id})...")
    os.system(f"qm create {vm_id} --name {vm_name} --memory 2048 --net0 virtio,bridge=vmbr0 --cores 2 --sockets 1")

    if os.path.exists(raw_path):
        print("Importando el disco convertido a Proxmox...")
        os.system(f"qm importdisk {vm_id} \"{raw_path}\" local-lvm")

        print("Añadiendo el disco a la configuración de la máquina virtual...")
        os.system(f"qm set {vm_id} --scsihw virtio-scsi-pci --scsi0 local-lvm:vm-{vm_id}-disk-0")

        print("Configurando el arranque de la máquina virtual...")
        os.system(f"qm set {vm_id} --boot c --bootdisk scsi0")

        print("Arrancando la máquina virtual...")
        os.system(f"qm start {vm_id}")

        cleanup_files()
    else:
        print(f"El archivo {vm_name}.raw no se encontró. Asegúrate de que se convirtió correctamente.")
        return

def convert_and_create_vm_from_ova(ova_path, vm_id):
    vm_name = os.path.splitext(os.path.basename(ova_path))[0]
    vm_name = sanitize_vm_name(vm_name)  # Sanitize the VM name
    ova_path_abs = os.path.abspath(ova_path)  # Get the absolute path
    print(f"Descomprimiendo el archivo {ova_path}...")
    os.system(f"tar -xvf \"{ova_path_abs}\"")

    vmdk_files = [f for f in os.listdir() if f.endswith('.vmdk')]
    if not vmdk_files:
        print("No se encontró ningún archivo .vmdk en la carpeta.")
        return

    vmdk_file = vmdk_files[0]
    convert_and_create_vm_from_vmdk(vmdk_file, vm_id)

def cleanup_files():
    print("Eliminando archivos descomprimidos y convertidos...")
    extensions_to_remove = ['.ovf', '.mf', '.vmdk', '.raw']
    for ext in extensions_to_remove:
        for filename in os.listdir('.'):
            if filename.endswith(ext) and os.path.exists(filename):
                os.remove(filename)
                print(f"Archivo {filename} eliminado.")

if __name__ == "__main__":
    while True:
        print("\nMenu Principal:")
        print("1- Descargar .ova de VulnHub")
        print("2- Crear VM con .ova")
        print("3- Crear VM con .vmdk")
        print("4- Salir")
        
        option = input("Seleccione una opción: ")

        if option == '1':
            download_ova_from_vulnhub()
        elif option == '2':
            ova_files = list_ova_files()
            if not ova_files:
                print("No se encontraron archivos .ova en la carpeta.")
                continue

            print("Archivos .ova disponibles:")
            for idx, ova_file in enumerate(ova_files, start=1):
                print(f"{idx}. {ova_file}")

            selected_index = int(input("Seleccione el número del archivo .ova que desea convertir: "))
            if 1 <= selected_index <= len(ova_files):
                selected_ova = ova_files[selected_index - 1]
                print(f"Ha seleccionado: {selected_ova}")

                vm_id = int(input("Introduce el ID de la máquina virtual: "))
                convert_and_create_vm_from_ova(selected_ova, vm_id)
            else:
                print("Selección inválida.")
        elif option == '3':
            vmdk_files = list_vmdk_files()
            if not vmdk_files:
                print("No se encontraron archivos .vmdk en la carpeta.")
                continue

            print("Archivos .vmdk disponibles:")
            for idx, vmdk_file in enumerate(vmdk_files, start=1):
                print(f"{idx}. {vmdk_file}")

            selected_index = int(input("Seleccione el número del archivo .vmdk que desea convertir: "))
            if 1 <= selected_index <= len(vmdk_files):
                selected_vmdk = vmdk_files[selected_index - 1]
                print(f"Ha seleccionado: {selected_vmdk}")

                vm_id = int(input("Introduce el ID de la máquina virtual: "))
                convert_and_create_vm_from_vmdk(selected_vmdk, vm_id)
            else:
                print("Selección inválida.")
        elif option == '4':
            break
        else:
            print("Opción inválida. Inténtalo de nuevo.")

    print("Saliendo del programa.")
