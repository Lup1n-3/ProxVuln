import os

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

if __name__ == "__main__":
    print_proxvuln_title()

def list_ova_files():
    ova_files = [f for f in os.listdir() if f.endswith('.ova')]
    return ova_files

def download_ova_from_vulnhub():
    url = input("Introduce el enlace para descargar el archivo .ova desde VulnHub: ")
    filename = url.split('/')[-1]
    print(f"Descargando {filename} desde VulnHub...")
    os.system(f"wget {url}")
    print("\nDescarga completada.")
    
def convert_and_create_vm(ova_path, vm_id):
    vm_name = os.path.splitext(os.path.basename(ova_path))[0]
    print(f"Descomprimiendo el archivo {ova_path}...")
    os.system(f"tar -xvf {ova_path}")

    # Buscar y convertir el archivo .vmdk
    vmdk_files = [f for f in os.listdir() if f.endswith('.vmdk')]
    if not vmdk_files:
        print("No se encontró ningún archivo .vmdk en la carpeta.")
        return

    vmdk_file = vmdk_files[0]  # Tomar el primer archivo .vmdk encontrado
    print(f"Convirtiendo el disco {vmdk_file} a un formato aceptado por Proxmox...")
    os.system(f"qemu-img convert -O raw {vmdk_file} {vm_name}.raw")

    # Crear la máquina virtual en Proxmox
    print(f"Creando la máquina virtual en Proxmox (ID: {vm_id})...")
    os.system(f"qm create {vm_id} --name {vm_name} --memory 2048 --net0 virtio,bridge=vmbr0 --cores 2 --sockets 1")

    if os.path.exists(f"{vm_name}.raw"):
        print("Importando el disco convertido a Proxmox...")
        os.system(f"qm importdisk {vm_id} {vm_name}.raw local-lvm")

        # Añadir el disco a la configuración de la máquina virtual
        print("Añadiendo el disco a la configuración de la máquina virtual...")
        os.system(f"qm set {vm_id} --scsihw virtio-scsi-pci --scsi0 local-lvm:vm-{vm_id}-disk-0")

        # Configurar el arranque de la máquina virtual
        print("Configurando el arranque de la máquina virtual...")
        os.system(f"qm set {vm_id} --boot c --bootdisk scsi0")

        print("Arrancando la máquina virtual...")
        os.system(f"qm start {vm_id}")

        cleanup_files()
    else:
        print(f"El archivo {vm_name}.raw no se encontró. Asegúrate de que se convirtió correctamente.")
        return

def find_imported_disk(vm_id):
    output = os.popen(f"qm config {vm_id}").read()
    lines = output.split("\n")
    for line in lines:
        if line.strip().startswith("ide0: local-lvm:"):
            disk_name = line.strip().split(":")[2].strip()
            return disk_name
    return None

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
        print("3- Salir")
        
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
                convert_and_create_vm(selected_ova, vm_id)
            else:
                print("Selección inválida.")
        elif option == '3':
            break
        else:
            print("Opción inválida. Inténtalo de nuevo.")

    print("Saliendo del programa.")
