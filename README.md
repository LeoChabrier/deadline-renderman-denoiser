# Deadline & RenderMan Denoiser
Production Ready deadline submitter and plug-in to denoise an EXR sequence using RenderMan's denoise tool.
All parameters exposed.

![Deadline](https://img.shields.io/badge/Deadline-10.x-blue)
![RenderMan](https://img.shields.io/badge/RenderMan-27.x-orange)
![Python](https://img.shields.io/badge/Python-3.x-green)
![OpenEXR](https://img.shields.io/badge/OpenEXR-3x-yellow)


## Requirements

- **Thinkbox Deadline 10+**
- **Renderman 27+**
- **Python 3.7+**
- **Exr sequence with required AOVs**

## Documentations
- [Deadline](https://docs.thinkboxsoftware.com/products/deadline/10.4/1_User%20Manual/manual/overview.html)
- [RenderMan](https://rmanwiki-27.pixar.com/)
- [Python](https://www.python.org/)
- [OpenEXR](https://openexr.com/en/latest/)
- [AOVs Requirements](https://rmanwiki-27.pixar.com/space/REN27/542232567/Denoiser+AOVs)

## Manual Installation

1. **Clone the repository** :
   ```bash
   git clone https://github.com/LeoChabrier/deadline-renderman-denoiser.git
   ```

2. **Copy to Deadline repository** :


   Copy _custom_ folder directly to your repository root folder.

3. **Optional** :


   In your Deadline monitor, go to _Tools > Power User Mode > Configure Scripts Menus > Import Menus_
   and import _menu/RenderManDenoiser.menu_ to see the submitter in Submit > 2D/Compositing in your _Deadline Monitor_.
   Else it will appear directly into _Submit > RendermanDenoiserSubmission_


<p align="center">
  <img width="460" height="300" src="images/image.png">
</p>

## Automatic Installation
   ```bash
   cd deadline-renderman-denoiser
   ./.scripts/Push-To-Repository.ps1
   ```

## Warning
   - When specifying the Frame List, you have to specify the _real frame range_ of your EXRs sequence. Example : seq001_sh0010_rendering_main_v001.[1001-1010].exr will lead to 1001-1010 in _Frame List_ parameter.

   - Ensure to respect industry standard frame pattern expected by denoise_batch.exe (.####.exr)

   - denoise_batch.exe is expecting lgt & lpe files to be in the same directory as the variance file is.

<p align="center">
  <img width="460" height="300" src="images/image-1.png">
</p>

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
