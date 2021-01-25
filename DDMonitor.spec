# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(['DD监控室.py'],
             pathex=[],
             binaries=[
                ('libvlc.dll', '.'),
                ('libvlccore.dll', '.'),
                ('plugins', 'plugins'),
             ],
             datas=[
                ('utils/ascii.txt', '.'),
                ('utils/help.html', '.'),
                ('utils/qdark.qss', 'utils'),
                ('utils/splash.jpg', 'utils'),
                ('utils/vtb.csv', 'utils'),
                ('scripts/run.bat', '.'),
            ],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='DDMonitor',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          icon='favicon.ico',
          console=False )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='DDMonitor')
