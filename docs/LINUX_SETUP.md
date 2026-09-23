# Linux Mint 22.3 Xfce setup for Mel's Mid-2012 13-inch MacBook Pro

Target Mac: MacBookPro9,2, Mid-2012 13-inch, Intel Core i5-3210M, 8 GB RAM, Intel HD 4000 graphics, currently running macOS Catalina.

This is a preparation and installation guide. It does not mean that Linux has been installed or tested on this Mac. Confirm every release, download, disk choice, and prompt on the screen before continuing.

## BACKUP FIRST (do not skip)

1. Make a current, tested backup of every important Catalina file. Prefer both a Time Machine backup and a separate copy of irreplaceable files to another disk or cloud storage.
2. Make sure you can restore the backup. Open a few files from it, and keep the backup disconnected while changing partitions when practical.
3. Save Catalina recovery information and any encryption/recovery keys. Do not erase or repartition the internal disk until the backup is known to work.
4. This guide recommends trying Linux from a live USB first and then dual-booting alongside Catalina. A full-disk Linux install is not the first approach here because it removes Catalina and increases the consequence of a disk mistake.

## 1. Download Linux Mint Xfce

1. On Catalina, open the official download page:

   https://www.linuxmint.com/download.php

2. Select the Linux Mint 22.3 Xfce edition. The official page is expected to offer an Xfce edition; confirm that the page currently lists the requested 22.3 release and Xfce image before downloading.
3. The ISO is approximately 3 GB. Treat the exact release number, filename, and byte size as time-sensitive: confirm them on the official page rather than relying on this guide for exact numbers.
4. Download only from the official Linux Mint page or its listed mirrors. If the page provides checksums or signatures, verify the downloaded ISO using the instructions currently published there. Do not use an ISO whose checksum does not match.
5. Keep enough free space for the ISO and for a USB drive of at least 8 GB. The USB will be erased.

## 2. Create a bootable USB on the Mac with BalenaEtcher

1. Download and install BalenaEtcher from its official site:

   https://etcher.balena.io/

2. Insert the USB drive. Confirm that it contains nothing you need; Etcher will overwrite it.
3. Open BalenaEtcher. Approve macOS security prompts only if you intentionally installed the official app.
4. Choose Flash from file, select the downloaded Linux Mint ISO, choose the correct USB drive, and select Flash.
5. Authenticate when macOS asks. Wait for flashing and validation to finish; do not unplug the USB during either step.
6. Eject the USB from Finder before rebooting. If macOS says the disk is unreadable after flashing, do not initialize or format it; that can be normal for a Linux boot disk. Eject it instead.

Security caution: a mistaken disk selection can destroy data. Check the USB capacity/name in Etcher and unplug other removable disks if that makes identification safer.

## 3. Boot and test the live USB before installing

1. Shut down the Mac completely.
2. Insert the Linux Mint USB.
3. Turn the Mac on and immediately hold the Option (Alt) key until the Apple Startup Manager appears.
4. Select the EFI Boot or external EFI/Linux entry for the USB. Do not select the internal Catalina disk for this test. If no USB entry appears, shut down and try another USB port, another freshly flashed USB, or re-check the ISO and Etcher validation.
5. Choose the option to start Linux Mint without installing (the live session). Nothing should be installed merely by starting the live session.
6. Test the things that matter before touching the installer:
   - Wi-Fi: connect to a trusted network, disconnect, and reconnect.
   - Keyboard, trackpad, screen brightness, sound, USB ports, sleep/wake, and battery charging.
   - Display stability with the Intel HD 4000 and ordinary web use.
   - The internal Catalina disk is visible only if you intentionally open it; do not modify it.
7. If Wi-Fi is missing, this Mac's Broadcom wireless card may need the `broadcom-sta-dkms` package after installation. The live session may not have that package available offline. Record the exact symptom and make sure you have a wired connection, USB tethering, or another way to get packages after installation.
8. To leave the live session, shut down from the Mint menu, remove the USB when the Mac is off, and start normally. Do not click Install Linux Mint until the backup and partition plan are ready.

## 4. Recommended first installation: dual-boot with Catalina

Dual-booting keeps Catalina available while Linux is evaluated. It is recommended here over erasing the disk. It still changes the partition table and boot process, so treat it as a destructive operation if performed incorrectly.

Before starting the installer:

1. In Catalina, finish backups and close all applications.
2. If FileVault or another disk-encryption scheme is enabled, understand how it affects resizing and recovery. Have the recovery key available. Do not guess at a recovery prompt.
3. Install pending Catalina updates first if appropriate, then shut down cleanly. Do not resize a disk while Catalina is running or while the filesystem reports errors.
4. Make a plan for the Linux size. Leave Catalina enough free space for macOS updates, applications, swap needs, and personal data. Never choose the entire disk or an existing Catalina/APFS partition unless you intentionally want to erase Catalina.
5. If the Mint installer offers to install alongside Catalina, read the partition preview carefully. Stop if the preview proposes erasing the disk, removing the Catalina/APFS container, or using the wrong disk.
6. If manual partitioning is required, use unallocated space created safely and identify partitions by size and filesystem. Do not format the EFI System Partition, the macOS recovery partition, or any Catalina/APFS volume. When uncertain, cancel and restore the backup plan before proceeding.
7. Keep the Mac connected to power. Maintain a reliable network if the installer requests updates or third-party software.
8. The installer may install a bootloader and change which system starts by default. This is expected for dual-boot, but boot behavior can vary on Intel Macs. Do not claim success until both Catalina and Mint have been started and checked.
9. After installation, restart with the USB removed. Use the Option key at power-on to choose between the internal macOS/Catalina startup volume and the Linux boot entry when needed.

A full-disk install is an alternative only after a verified backup and an explicit decision that Catalina is no longer needed. It erases macOS and its recovery path; this guide does not recommend or perform that choice.

## 5. First Mint updates and Wi-Fi driver

Open Terminal in the installed Mint system. Run:

    sudo apt update
    sudo apt full-upgrade -y
    sudo apt install -y linux-firmware

Reboot after a kernel or firmware update:

    sudo reboot

If Wi-Fi does not work after installation, first obtain temporary internet access using Ethernet, USB tethering, or another supported method. Then run:

    sudo apt update
    sudo apt install -y broadcom-sta-dkms
    sudo reboot

After reboot, check the Network Manager menu. If the package cannot be found, do not substitute a random driver or third-party download. Check the Mint release repositories, the live-session notes, and the hardware identifier first. DKMS builds are kernel-specific; read any build error and resolve it before rebooting again.

Useful identification commands (read-only):

    lspci -nnk | grep -A3 -i -E 'network|wireless'
    uname -a
    inxi -Nxx

## 6. Native Docker Engine and Compose plugin

Use Docker's official Ubuntu Engine instructions as the reference path:

https://docs.docker.com/engine/install/ubuntu/

Linux Mint is Ubuntu-based, but Mint's own version and Ubuntu base codename can differ. The commands below deliberately check the base first. Do not blindly add an Ubuntu repository if the check is missing, unexpected, or not supported by the Docker documentation.

### 6.1 Check the Mint and Ubuntu base

Run:

    . /etc/os-release
    printf 'ID=%s\\nVERSION_ID=%s\\nVERSION_CODENAME=%s\\nUBUNTU_CODENAME=%s\\n' "$ID" "$VERSION_ID" "${VERSION_CODENAME:-}" "${UBUNTU_CODENAME:-}"
    dpkg --print-architecture

Continue only if `ID=linuxmint`, `UBUNTU_CODENAME` is present, and the Docker Ubuntu documentation currently supports that Ubuntu base. For a Mint release whose base is not listed or whose repository does not offer Docker packages, stop and follow the current Docker/Mint compatibility guidance rather than guessing a codename. Architecture matters: this Mac is Intel, so `dpkg --print-architecture` is normally `amd64`; verify it.

For the remaining commands, set the repository codename from the checked Ubuntu base:

    DOCKER_UBUNTU_CODENAME="$UBUNTU_CODENAME"
    test -n "$DOCKER_UBUNTU_CODENAME" || { echo 'No Ubuntu base codename; stop and verify compatibility.'; exit 1; }
    echo "$DOCKER_UBUNTU_CODENAME"

### 6.2 Add Docker's repository key and apt repository safely

These commands follow Docker's current Ubuntu repository method. Review the official page before running them if its key or repository instructions have changed:

    sudo apt update
    sudo apt install -y ca-certificates curl
    sudo install -m 0755 -d /etc/apt/keyrings
    sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    sudo chmod a+r /etc/apt/keyrings/docker.asc
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $DOCKER_UBUNTU_CODENAME stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt update
    apt-cache policy docker-ce

If `apt-cache policy docker-ce` shows no candidate, stop. Remove the repository file only if you added it for this attempt, then verify the Mint/Ubuntu base and the Docker documentation:

    sudo rm -f /etc/apt/sources.list.d/docker.list
    sudo apt update

Do not disable apt signature checks, paste a key from an untrusted site, or mix Debian and Ubuntu repositories.

### 6.3 Install Engine, Buildx, and Compose

Only after the candidate check succeeds:

    sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    sudo systemctl enable --now docker

The Docker daemon is privileged. Add the normal login user to the `docker` group only if that root-equivalent access is acceptable on this personal machine:

    sudo usermod -aG docker "$USER"

Log out of the graphical session and log back in, or start a new shell with:

    newgrp docker

Test Engine and the Compose plugin:

    docker run hello-world
    docker compose version

The first command downloads and runs Docker's hello-world image; it requires network access. If `docker` permission errors remain after `newgrp`, log out and in again. Do not use `sudo docker` as a workaround without understanding that it uses a different configuration and can hide group/session problems.

Docker architecture caveat: this Mac's native architecture is Intel `amd64`. ARM-only images from an Oracle ARM VM may not run natively here without compatible multi-architecture images or emulation. Prefer images that publish both `amd64` and `arm64` manifests, and review image provenance before use.

## 7. Optional remote heavy sandbox: Oracle Cloud Always Free ARM VM

A remote Oracle Cloud Always Free ARM VM can be a heavier sandbox for KYLA when this 8 GB Mac is constrained. The stated Always Free capacity can be up to 4 OCPU and 24 GB RAM for eligible ARM resources, subject to Oracle's current terms.

Official details:

https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier.htm

Availability, regional capacity, quotas, account eligibility, and Oracle's terms can vary. Confirm the current console limits and the selected image before creating anything. ARM instances use `arm64/aarch64`, not this Mac's native `amd64/x86_64`; use ARM-compatible operating-system packages and container images, or explicitly use multi-architecture images. Secure the VM with SSH keys (never paste private keys into a repository), least-privilege firewall rules, updates, and a plan for stopping or deleting resources that are no longer needed. A cloud VM is not automatically private or free outside the stated eligibility and capacity limits.

## 8. KYLA-specific notes

KYLA's Docker sandboxes cover exactly these seven core agents:

    claude
    codex
    copilot
    cursor
    docker-agent
    droid
    shell

Keep the R13 review gate mandatory. Do not treat a successful container build, a successful `hello-world` run, or an ARM remote VM as approval to bypass R13 review. Do not put API keys, tokens, SSH private keys, cloud credentials, or other secrets in this repository, Dockerfiles, shell history, or documentation.

## Concise verification checklist

- [ ] A current Catalina backup exists and has been tested.
- [ ] The official Mint download page currently lists the requested Linux Mint 22.3 Xfce edition; filename, exact size, checksum, and release details were confirmed there.
- [ ] The ISO checksum/signature was verified when the official page provided the relevant instructions.
- [ ] BalenaEtcher completed flashing and validation to the intended USB; no other disk was erased.
- [ ] The Mac booted the USB with Option (Alt), and the live session was tested before installation.
- [ ] Wi-Fi was tested; if unavailable, a safe post-install path to `broadcom-sta-dkms` was identified.
- [ ] The dual-boot partition preview was reviewed and does not erase Catalina/APFS or the EFI/recovery partitions.
- [ ] After installation, both Catalina and Mint boot successfully. (This guide does not claim that installation was performed.)
- [ ] Mint updates completed; Docker base codename and architecture were checked before adding Docker's repository.
- [ ] `docker run hello-world` and `docker compose version` succeeded, if Docker was installed.
- [ ] Any Oracle VM was confirmed as eligible/available, secured, and treated as ARM `arm64`.
- [ ] KYLA uses exactly the seven listed Docker sandboxes and the R13 review gate remains mandatory.
