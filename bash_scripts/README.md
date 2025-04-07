A collection of bash scripts I've made for various purposes.

1. `bootfs-monitor.sh` - Monitors the boot file system for changes using the Linux kernel's inotify feature, and if it changes, triggers a backup.
2. `create_nvidia_nodes.sh` - Create the nvidia nodes for udev... was used to troubleshoot a problem with nvidia's stock udev rules.
3. `hidrawmatch.sh` - A script to match hidraw devices to their corresponding tty devices.
4. `kernel-cleaner.sh` - A script to clean up old kernels.
5. `windowid.sh` - A script to get the window ID of the currently focused window.
6. `compile_ffmpeg_fedora` - A script to compile ffmpeg on Fedora with NVENC support. Will also handle updates and dependencies. FFMPEG really isn't at its fullest if you don't compile it yourself.
