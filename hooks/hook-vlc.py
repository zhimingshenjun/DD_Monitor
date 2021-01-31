# -*- coding: utf-8 -*-
"""PyInstaller python-vlc hook
ref: https://pyinstaller.readthedocs.io/en/stable/hooks.html
"""
from PyInstaller.compat import is_win
from vlc import dll as vlc_dll
from vlc import plugin_path
import os


datas = []
binaries = []
hiddenimports = []
plugins_dlls = [
    # (subdir, fname)
    ('access', 'libfilesystem_plugin'),

    ('codec', 'libdxva2_plugin'),
    ('codec', 'libavcodec_plugin'),
    ('audio_output', 'libdirectsound_plugin'),
    ('audio_mixer', 'libfloat_mixer_plugin'),

    ('video_chroma', 'libswscale_plugin'),
    ('video_output', 'libdirect3d11_plugin'),
    ('video_output', 'libdrawable_plugin'),
    ('video_output', 'libdirectdraw_plugin'),
]


def gen_plugins_binary(vlc_root, dest, fnames=plugins_dlls, ext='.dll', use_subdir=True):
    plugin_binaries = []
    for (subdir, fname) in fnames:
        # plugin_path: 存放插件的目录
        #   win: 'VLC/plugins/'
        #   mac: 'VLC.app/Contents/MacOS/plugins/'
        if use_subdir:
            plugin_root = os.path.join(vlc_root, 'plugins', subdir)
        else:
            plugin_root = os.path.join(vlc_root, 'plugins')

        lib_path = os.path.join(plugin_root, fname + ext)
        if not os.path.isfile(lib_path):
            import warnings
            warnings.warn(f'VLC plugin {fname} not found!', ResourceWarning)
            continue

        plugin_binaries.append((lib_path, dest))

    return plugin_binaries


if is_win:
    binaries = [
        (str(vlc_dll._name), '.'),
        # (os.path.join(plugin_path, 'libvlc.dll'), '.'),
        (os.path.join(plugin_path, 'libvlccore.dll'), '.'),
    ]
    binaries += gen_plugins_binary(plugin_path, 'plugins')
# end is_win
