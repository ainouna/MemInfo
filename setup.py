from distutils.core import setup
import setup_translate

pkg = 'Extensions.MemInfo'
setup (name = 'enigma2-plugin-extensions-meminfo',
       version = '1.04',
       description = 'memory monitor',
       packages = [pkg],
       package_dir = {pkg: 'plugin'},
       package_data = {pkg: ['*.png', 'locale/*.pot', 'locale/*/LC_MESSAGES/*.mo']},
       cmdclass = setup_translate.cmdclass, # for translation
      )
