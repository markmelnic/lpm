import glob, time, requests
import pandas as pd
from lxml import html
from zipfile import ZipFile
from PIL import Image

from .utils import *

KMZ_URL = "https://datapub.gfz-potsdam.de/download/10.5880.GFZ.1.4.2016.001/NewWorldAtlas_ArtificialSkyBrightness.kmz"
KMZ_FILENAME_DEFAULT = "NewWorldAtlas_ArtificialSkyBrightness.kmz"
ZIP_KMZ_IMG_FOLDER = 'files'
KMZ_GLOBAL_IMAGE = 'map.png'
DF_COLUMNS = ['index', 'image', 'draw_order', 'north', 'south', 'east', 'west', 'rotation']

pd.options.mode.chained_assignment = None

class KMZ:
    def __init__(self, csv=False) -> None:
        try:
            kmz_filename = glob.glob('*.kmz')[0]
        except IndexError:
            r = requests.get(KMZ_URL)
            open(KMZ_FILENAME_DEFAULT, 'wb').write(r.content)
            kmz_filename = KMZ_FILENAME_DEFAULT
        self.kmz_zip = ZipFile(kmz_filename, 'r')
        self.kml_file = self.kmz_zip.open('doc.kml').read()

        self.globe_matrix = []
        if csv:
            self._load_df(to_csv=csv)
        else:
            self._load_df()
        self._arrange_df()

    def _load_data(self, ):
        kml_content = html.fromstring(self.kml_file)
        data = []
        for item in kml_content.cssselect('Document GroundOverlay'):
            image = item.cssselect('name')[0].text_content()
            index = image[23:-4]
            draw_order = item.cssselect('drawOrder')[0].text_content()
            coords = item.cssselect('LatLonBox')[0]
            north = float(coords.cssselect('north')[0].text_content())
            south = float(coords.cssselect('south')[0].text_content())
            east = float(coords.cssselect('east')[0].text_content())
            west = float(coords.cssselect('west')[0].text_content())
            rotation = coords.cssselect('rotation')[0].text_content()
            data.append([index, image, draw_order, north, south, east, west, rotation])
        return data

    def _load_df(self) -> None:
        self.df = pd.DataFrame(self._load_data(), columns=DF_COLUMNS)
        self.df.sort_values(by='north', ascending=False, inplace=True)

    def _arrange_df(self) -> None:
        for i, row in self.df.iterrows():
            sub_df = self.df.loc[(self.df['north'] == row['north']) & (self.df['south'] == row['south'])]
            if not sub_df.empty:
                sub_df.sort_values(by='west', inplace = True)
                self.globe_matrix.append(sub_df)
                self.df.drop(sub_df.index, inplace = True)

    def _generate_image(self, images: list, fullvh: bool=False, vertical: bool=False, horizontal: bool=False):
        if horizontal:
            widths, heights = zip(*(img.size for img in images))
            total_width = sum(widths)
            max_height = max(heights)

            new_image = Image.new('RGB', (total_width, max_height))
            x_offset = 0
            for img in images:
                new_image.paste(img, (x_offset,0))
                x_offset += img.size[0]

        elif vertical:
            widths, heights = zip(*(img.size for img in images))
            max_width = max(widths)
            total_height = sum(heights)

            new_image = Image.new('RGB', (max_width, total_height))
            y_offset = 0
            for img in images:
                new_image.paste(img, (0,y_offset))
                y_offset += img.size[1]

        elif fullvh:
            vertical_set = [self._generate_image(image, horizontal=True) for image in images]
            new_image = self._generate_image(vertical_set, vertical=True)

        return new_image

    def coords_item(self, coords: list) -> list:
        if coords[0] > 0: # first 10
            gset = [None, -7]
            if coords[1] > 0: # last 21
                sset = [22, None]
            else:
                sset = [None, -21]
        else: # last 7
            gset = [10, None]
            if coords[1] > 0: # last 21
                sset = [22, None]
            else:
                sset = [None, -21]

        for item in self.globe_matrix[gset[0]:gset[1]]:
            for i, row in item.iloc[sset[0]:sset[1]].iterrows():
                if (row['north'] >= coords[0] >= row['south']) and (row['west'] <= coords[1] <= row['east']):
                    return row.tolist()

    def load_images(self, images: list, single: bool=False, neighbours: bool=False) -> list:
        if single:
            if neighbours:
                f = [images[:-7], images[-4:]]
                c = int(images[:-4][-3:])
                images = [
                        [c+42 , c+43, c+44],
                        [c-1  , c    , c+1],
                        [c-44, c-43, c-42],
                    ]

                edges = [0, 0, 0, 0]
                for item in self.globe_matrix:
                    for i, row in item.iterrows():
                        row = row.tolist()
                        if int(row[0]) == images[0][0]:
                            edges[0] = row[3]
                            edges[3] = row[6]
                        elif int(row[0]) == images[2][2]:
                            edges[1] = row[4]
                            edges[2] = row[5]

                for i, s in enumerate(images):
                    for j, g in enumerate(s):
                        images[i][j] = f[0]+str(g)+f[1]

                return edges, self._generate_image(self.load_images(images), fullvh=True)
            else:
                return Image.open(self.kmz_zip.open(ZIP_KMZ_IMG_FOLDER+"/"+images))
        else:
            if images:
                if type(images[0]) == list:
                    kmz_imgs = [[Image.open(self.kmz_zip.open(ZIP_KMZ_IMG_FOLDER+"/"+image)) for image in image_set] for image_set in images]
                else:
                    kmz_imgs = [Image.open(self.kmz_zip.open(ZIP_KMZ_IMG_FOLDER+"/"+image)) for image in images]
            else:
                kmz_imgs = [Image.open(self.kmz_zip.open(image)) for image in self.kmz_zip.namelist() if image.split("/")[0] == ZIP_KMZ_IMG_FOLDER]
            return kmz_imgs

    def save_images(self, images: list = []) -> None:
        '''
        Save images to disk or save all images in the kmz file
        '''

        if not images:
            images = [self.load_images(matrix["image"].tolist()) for matrix in self.globe_matrix]

        filename = f'KMZ{time.strftime("%Y%m%d-%H%M%S")}.png'
        self._generate_image(images, fullvh=True).save(filename)
