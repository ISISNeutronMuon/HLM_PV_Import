# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['HlmManager.py'],
             pathex=[],
             binaries=[],
             datas=[
				("ServiceManager/GUI/layouts", "GUI/layouts"),
				("ServiceManager/GUI/assets", "GUI/assets"),
				("icon.ico", ".")
			],
             hiddenimports=['win32timezone'],
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
          name='HlmManager',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False,
		  icon='icon.ico' )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='HlmManager')
