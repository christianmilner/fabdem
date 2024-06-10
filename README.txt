# FABDEM Tile Finder Plugin

## Overview

FABDEM Tile Finder is a QGIS plugin designed to help users locate and manage FABDEM tiles that intersect with a specified geographic extent. This plugin simplifies the process of identifying and working with relevant DEM tiles within a given region.

## Features

- **Select FABDEM Tile Folder:** Choose a directory containing FABDEM tiles.
- **Select Geographic Extent:** Use a polygon layer to define the area of interest.
- **Find Intersecting Tiles:** Identify FABDEM tiles that intersect with the specified extent.
- **Progress Tracking:** Monitor the progress of tile search operations with a progress bar.
- **Add Intersecting Tiles to QGIS:** Automatically add intersecting tiles to the QGIS project for further analysis.

## Installation

1. Download or clone this repository.
2. Open QGIS and navigate to `Plugins` > `Manage and Install Plugins...`
3. Click on the `Install from ZIP` button.
4. Select the downloaded ZIP file and click `Install Plugin`.

## Usage

1. Activate the plugin from the QGIS plugin manager.
2. Click on the `FABDEM Tile Finder` icon in the toolbar.
3. In the dialog:
   - Select the folder containing your FABDEM tiles.
   - Choose a polygon layer to define the area of interest.
   - Click `OK` to start the process.
4. The plugin will display the progress and add the intersecting tiles to the QGIS project.

## Requirements

- QGIS 3.x
- Python 3.x
- Dependencies: `rasterio`, `geopandas`, `shapely`, `rioxarray`, `fiona`

## Contributing

Contributions are welcome! Please fork this repository and submit pull requests for any improvements or bug fixes.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

Special thanks to the QGIS and FABDEM communities for their continuous support and contributions.

## Contact

For any issues or feature requests, please create an issue in this repository or contact [Your Name](mailto:your-email@example.com).

---

![QGIS](https://img.shields.io/badge/QGIS-3.x-green)
![Python](https://img.shields.io/badge/Python-3.x-blue)
