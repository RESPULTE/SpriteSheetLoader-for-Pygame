import pygame
from math import ceil
from os import listdir, PathLike
from typing import Dict, List, Tuple
from os.path import realpath, join, isdir, sep
from Utility.screen_saver import SaveScreen, Displayer
from Utility.utility import draw_grid


# {"bob": {"idle": [pygame.Surface1, pygame.Surface2], "run": [pygame.Surface3, pygame.Surface4]}}
AnimationDict = Dict[str, Dict[str, List[pygame.Surface]]]
Size          = Tuple[int, int]


class SpriteSheetLoader:

    '''generate surfaces using the spritesheet file's name as the id with the given folder path'''

    def __init__(self, mainImgFolderPath: PathLike, canvasSize: Size, color_to_kill: Tuple[int, int, int]):

        # mandatory set up for the spritesheet loader
        self.mainImgFolderPath = realpath(join(sep, *mainImgFolderPath.split("/")))
        self.canvasSize = canvasSize
        self.color_to_kill = color_to_kill

        # Handle possible exceptions
        if not isdir(self.mainImgFolderPath):
            raise FileNotFoundError(f"The folder path provided is invalid: {self.mainImgFolderPath}")
        if len(color_to_kill) != 3:
            raise ValueError("The color_to_kill provided must be a tuple of 3 RGB values!")
        if not all(val in range(0, 256) for val in color_to_kill):
            raise ValueError("The color_to_kill provided must be a value between 0 to 255!")       

        self.total_animation_dict = {} 
        # example dictionary config for the generated animation dict


    def prepare_spritesheet(self, 
        folderName: str, 
        spriteDimensions: Size
        ) -> AnimationDict:

        spritesheet_directory = join(self.mainImgFolderPath, folderName)
        sprite_w, sprite_h = (x * self.canvasSize for x in spriteDimensions)

        # loop through every img_file/action in the given folder and load its respective images
        animation_dict = {}
        for spriteFileName in listdir(spritesheet_directory):

            # try loading the file, if the file somehow acnnot be loaded, just skip it and log an error msg
            try:
                spritesheet = pygame.image.load(join(spritesheet_directory, spriteFileName)).convert()
                spritesheet.set_colorkey(self.color_to_kill)
                spritesheet_w, spritesheet_h = spritesheet.get_size()
            except:
                print(f"{spriteFileName} cannot be loaded!")
                continue

            # check if the specified dimension of the spritesheet is the as the given sprite dimension 
            if spritesheet_h != sprite_h:
                raise Exception(f"The height of <{spriteFileName}>: {spritesheet_h} does not equal to the provided sprite size: {sprite_h}!")
            if spritesheet_w % sprite_w != 0:
                raise Exception(f"The width of <{spriteFileName}>: {spritesheet_w} does not equal to the provided sprite size: {sprite_w}!")

            # create a temporary list to contain the surfaces of the specific action
            surface_list = []
            for x in range(0, spritesheet_w, sprite_w):
                sprite_surf = pygame.Surface((sprite_w, sprite_h))
                sprite_surf.blit(spritesheet, (0, 0), (x, 0, sprite_w, sprite_h))
                surface_list.append(sprite_surf)

            # use the name of the file as the action's name
            animation_dict[str(spriteFileName).split('.')[0]] = surface_list

        # cache the surfaces in a central dictionary, useful for viewing / checking later
        self.total_animation_dict[folderName] = animation_dict

        return animation_dict


@SaveScreen('Spritesheet')
class SpriteSheetDisplayer(Displayer):

    def __init__(self, animation_dict: AnimationDict, canvasSize: Size, maxActionPerPage: int = 12):
        self.animation_dict    = animation_dict
        self.canvasSize        = canvasSize
        self.maxActionPerPage  = maxActionPerPage

        self.surf_x, self.surf_y = 0, 0
        self.surf_w, self.surf_h = 0, 0
        self.surf_list           = None
        self.total_page          = 0
        self._currentPageIndex   = 0

        self.init_spritesheet()

        self.show()


    def init_spritesheet(self):
        self.set_spritesheet_size()
        self.draw_spritesheet()
        self.rescale_spritesheet()
        self.set_spritesheet_position()
        self.surf = self.surf_list[0]


    def set_spritesheet_size(self):
        # some setup for the dimensions of the seperate surface
        total_action_list  = [action for action_list in self.animation_dict.values() for action in action_list.values()]
        sorted_action_list = sorted(total_action_list, key=lambda surf_list: surf_list[0].get_width() * len(surf_list), reverse=True)
        self.surf_w        = sum(surf.get_width() for surf in sorted_action_list[0]) + self.canvasSize
        self.surf_h        = len(total_action_list) * self.canvasSize if len(total_action_list) <= self.maxActionPerPage else self.maxActionPerPage * self.canvasSize 
        self.total_page    = ceil(len(total_action_list) / self.maxActionPerPage) 
        self.surf_list     = [pygame.Surface((self.surf_w, self.surf_h)) for i in range(self.total_page)]


    def rescale_spritesheet(self):
        # resize the sprite surface if it's larger than the window's size
        if self.surf_w > self.win_w or self.surf_h > self.win_h:
            ratio_w = self.win_w / self.surf_w
            ratio_h = self.win_h / self.surf_h
            ratio = min(ratio_w, ratio_h) 
            if self.maxActionPerPage < 6:
                ratio *= 0.75
            for ind, surf in enumerate(self.surf_list):
                self.surf_list[ind] = pygame.transform.scale(surf, (int(self.surf_w * ratio), int(self.surf_h * ratio))) 
            self.surf_w, self.surf_h = self.surf_list[0].get_size()


    def set_spritesheet_position(self):
        self.surf_x = (self.win_w - self.surf_w) // 2
        self.surf_y = (self.win_h - self.surf_h) // 2


    def draw_spritesheet(self):
        # blit the sprite name onto sprite_surf
        # img_row: keep track of the row that its blitting on
        # needs to be seperate out, as for loops resets it's enumerator every iteration
        action_index   = 0
        page_index     = 0
        for sprite_name, animation_dict in self.animation_dict.items():
            sprite_text = self.text.create_txt(sprite_name, font_color='gold')
            self.surf_list[page_index].blit(sprite_text.surf, (10, action_index * self.canvasSize + 10))

            # blit the sprite's action_name onto sprite_surf
            for action, surface_list in animation_dict.items():
                action_text = self.text.create_txt(action)
                if action_text.get_width() > self.canvasSize:
                    action_text.surf = pygame.transform.scale(action_text.surf, (self.canvasSize-5, action_text.get_height()-5))
                action_rect = action_text.get_rect(center=(self.canvasSize//2, (action_index * self.canvasSize) + self.canvasSize//2))
                self.surf_list[page_index].blit(action_text.surf, (action_rect.x, action_rect.y))

                # blit the actual image of the sprite onto the sprite_surf
                for col, surf in enumerate(surface_list):
                    # using the width & height of the sprite itself/given to position the sprite on the sprite_surf accordingly
                    # < +self.canvasSize> to skip the first row of the grid for the action's name
                    # no matter the size of the sprite
                    x = col * surf.get_width() + self.canvasSize
                    y = action_index * surf.get_height()
                    self.surf_list[page_index].blit(surf, (x, y))

                    # numbering for the frame 
                    ind_text = self.text.create_txt(str(col), font_color='red')
                    self.surf_list[page_index].blit(ind_text.surf, (x+10, y+3))
                
                # increment the index after drawing the whole row of the sprite
                # and check whether the action_index is the maximum allowed row/action per page and if its not the last page
                # if so, draw a grid over the entire surface, reset the action to zero and increment the page index
                action_index += 1 
                if action_index >= self.maxActionPerPage and page_index != (self.total_page - 1):
                    grid_surf = draw_grid(self.surf_list[page_index], (self.canvasSize, self.canvasSize), (255, 255, 255))
                    self.surf_list[page_index] = grid_surf
                    page_index  += 1 
                    action_index = 0

        # drawing the grid for the last surface 
        # leaving this out of the for loop
        # the best way to do it without repeatedly drawing over the last surface
        # can be put inside the for-loop, but at the cost of adding another conditional check for the page index
        # and possibly needing a boolean flag to stop the for-loop from drawing the grid on the last surface again and again
        # in essence, not worth it ://, would much rather just repeat the code here at the end 
        grid_surf = draw_grid(self.surf_list[page_index], (self.canvasSize, self.canvasSize), (255, 255, 255))
        self.surf_list[page_index] = grid_surf


    def handle_user_input(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self._currentPageIndex = (self._currentPageIndex + 1) % self.total_page
            self.surf = self.surf_list[self._currentPageIndex]
            
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self._currentPageIndex = (self._currentPageIndex - 1) % self.total_page

            if event.key == pygame.K_RIGHT or event.key == pygame.K_SPACE:
                self._currentPageIndex = (self._currentPageIndex + 1) % self.total_page
        
            self.surf = self.surf_list[self._currentPageIndex]

    def draw(self):
        self.window.fill(self.DARK_GREY)
        self.window.blit(self.surf, (self.surf_x, self.surf_y))


    def update(self, dt):
        pass 



def main():
    test = SpriteSheetLoader("Users/USER/Desktop/game_engine/spriteloader_test", canvasSize=256, color_to_kill=(255, 255, 255))
    test.prepare_spritesheet("lmao", (1, 1))
    test.prepare_spritesheet("popop2", (1,1))
    SpriteSheetDisplayer(test.total_animation_dict, 256, 1)

if __name__ == '__main__':
    main()