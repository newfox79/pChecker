import os
import shutil

from PIL import ImageDraw, Image
import cv2
import numpy as np
import imagehash
from MSOCONSTANTS import ppShapeFormatJPG

from PresentationExamLayouts import PresentationExamLayouts as Layouts
import inspect


class PresentationExamImages(object):
    def __init__(self, presentation, utils):
        super().__init__()
        self._Presentation = presentation
        self._Utils = utils
        self._layouts = inspect.getmembers(Layouts, predicate=inspect.isfunction)

    @staticmethod
    def __skeleton_rectangle(draw, shape_dimensions, color, outline):
        return draw.rectangle(
            [shape_dimensions['left'],
             shape_dimensions['top'],
             shape_dimensions['width'] + shape_dimensions['left'],
             shape_dimensions['height'] + shape_dimensions['top']],
            fill=color,
            outline=outline
        )

    def __generate_images_skeleton(self, return_path=False, return_bool=False):
        if not os.path.exists('temp'):
            os.mkdir('temp')
        for Slide in self._Presentation.Slides:
            skeleton = Image.new("RGB",
                                 color="#ffffff",
                                 size=(self._Utils.convert_points_px(self._Presentation.PageSetup.SlideWidth),
                                       self._Utils.convert_points_px(self._Presentation.PageSetup.SlideHeight))
                                 )
            skeleton_path = os.path.abspath(f"temp/skeleton_{Slide.SlideIndex}.jpg")
            skeleton_draw = ImageDraw.Draw(skeleton)
            for Shape in Slide.Shapes:
                shape_dimensions = self._Utils.get_shape_dimensions(Shape)
                if self._Utils.is_text(Shape) is True:
                    self.__skeleton_rectangle(skeleton_draw, shape_dimensions, "yellow", "red")
                elif self._Utils.is_text(Shape) is None:
                    self.__skeleton_rectangle(skeleton_draw, shape_dimensions, "orange", "yellow")
                elif self._Utils.is_image(Shape) is True:
                    self.__skeleton_rectangle(skeleton_draw, shape_dimensions, "blue", "yellow")
                else:
                    self.__skeleton_rectangle(skeleton_draw, shape_dimensions, "red", "yellow")
                skeleton.save(skeleton_path)
            if return_path is True:
                yield skeleton_path
        if return_bool is True:
            return True

    def __generate_images_layout(self, lt="layout_1"):
        """
        Experimental
        :return: None
        """
        if not os.path.exists('temp'):
            os.mkdir('temp')
        width = self._Utils.convert_points_px(self._Presentation.PageSetup.SlideWidth)
        height = self._Utils.convert_points_px(self._Presentation.PageSetup.SlideHeight)
        result = []
        layout = self._layouts[lt][1](width, height)
        for slide in layout:
            image_path = os.getcwd() + "\\temp\\" + f"image_{slide}.png"
            cv2.imwrite(image_path, 255 * np.ones((height, width, 3), np.uint8))
            image = cv2.imread(image_path)
            overlay = image.copy()
            for i in layout[slide]['images']:
                l, t, w, h = int(i[0]), int(i[1]), int(i[2]), int(i[3])
                cv2.rectangle(overlay, (l, t), (w + l, h + t), (0, 255, 0), -1)
            for t in layout[slide]['text_blocks']:
                l, t, w, h = int(t[0]), int(t[1]), int(t[2]), int(t[3])
                cv2.rectangle(overlay, (l, t), (w+l, h+t), (255, 0, 0), -1)
            cv2.addWeighted(overlay, 0.7, image, 0.3, 0, image)
            cv2.imwrite(image_path, image)
            result.append(image_path)
        return result

    def __get_original_images_from_presentation(self, return_path=False, return_bool=False):
        if not os.path.exists('shapes_images'):
            os.mkdir('shapes_images')
        counter = 0
        for Slide in self._Presentation.Slides:
            for Shape in Slide.Shapes:
                if self._Utils.is_image(Shape):
                    counter += 1
                    path = os.getcwd() + f"\\shapes_images\\picture_{counter}.jpg"
                    Shape.Export(path, ppShapeFormatJPG)
                    if return_path:
                        yield path
        if return_bool:
            return True

    def __compare_images(self):
        path_to_shape_images = list(self.__get_original_images_from_presentation(return_path=True))
        compare_images_counter = 0
        for original_image_name in os.listdir(os.getcwd() + "\\original_images\\"):
            for shape_image_path in path_to_shape_images:
                original_image = Image.open(os.getcwd() + "\\original_images\\" + original_image_name)
                shape_image = Image.open(shape_image_path)
                if imagehash.average_hash(original_image) == imagehash.average_hash(shape_image):
                    compare_images_counter += 1
                    path_to_shape_images.remove(shape_image_path)
                    break
                elif imagehash.average_hash(shape_image) - imagehash.average_hash(original_image) <= 10:
                    compare_images_counter += 1
                    path_to_shape_images.remove(shape_image_path)
                    break
        else:
            #print(path_to_shape_images)
            if len(path_to_shape_images) <= 2:
                shutil.rmtree(os.getcwd() + "\\shapes_images\\")
                return True
            shutil.rmtree(os.getcwd() + "\\shapes_images\\")
            return False

    def __generate_images_screenshots(self, return_path=False, return_bool=False):
        if not os.path.exists('temp'):
            os.mkdir('temp')
        for Slide in self._Presentation.Slides:
            screenshot_path = os.path.abspath(f"temp/slide_{Slide.SlideIndex}.jpg")
            Slide.Export(screenshot_path, "JPG")
            if return_path is True:
                yield screenshot_path
        if return_bool:
            return True

    def compare(self):
        if os.listdir(os.getcwd() + "\\original_images\\"):
            return self.__compare_images()
        else:
            return "Не загружены изображения."

    def get(self, typeof="exact_match", return_path=True, lt="layout_1"):
        if typeof == "exact_match":
            if return_path:
                return list(self.__generate_images_screenshots(return_path=True))
            else:
                return self.__generate_images_screenshots(return_bool=True)
        elif typeof == "skeleton":
            if return_path:
                return list(self.__generate_images_skeleton(return_path=True))
            else:
                return self.__generate_images_skeleton(return_bool=True)
        elif typeof == "layout":
            return self.__generate_images_layout(lt)
        else:
            return "Mismatched type of generation"
