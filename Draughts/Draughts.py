
import math
import pygame
from sys import exit

pygame.init()

WIDTH = 800
HEIGHT = 800
MAP_SIZE = 10
CELL_SIZE = 64
PIECE_SIZE = 48

class Path():
    def __init__(self, pos=(0,0)):
        self.pos = pos
        self.killNum = 0
        self.killPiece = None
        self.next = []

    def SetPos(self, pos):
        self.pos = pos

    def SetKillNum(self):
        for child in self.next:
            child.SetKillNum()
        current_kill = 1 if self.killPiece else 0
        max_child = max([child.killNum for child in self.next]) if self.next else 0
        self.killNum = current_kill + max_child
        if self.next:
            max_kill = max(child.killNum for child in self.next)
            self.next = [child for child in self.next if child.killNum == max_kill]

    def GetNext(self) -> list:
        if len(self.next) == 0:
            return None
        return self.next

    def GetPos(self) -> tuple:
        return self.pos

    def Reset(self):
        self.pos = (0,0)
        self.killNum = 0
        self.killPiece = None
        self.next = []

    def AddNext(self, nextNode_s: list):
        for node in nextNode_s:
            self.next.append(node)

    def SetKillPiece(self, piece):
        self.killPiece = piece

    def GetKillPiece(self):
        return self.killPiece

class ObjectPool():
    def __init__(self, obj, size):
        self.pool = [obj() for _ in range(size)]
        self.obj = obj
        self.extra = []
        self.index = 0

    def Get(self):
        if self.index >= len(self.pool):
            self.extra.append(self.obj())
            return self.extra[self.index - len(self.pool)]
        obj = self.pool[self.index]
        self.index += 1
        return obj

    def Reset(self):
        del self.extra[:]
        self.index = 0
        for obj in self.pool:
            obj.Reset()

class Piece():
    def __init__(self, color, pos):
        self.pos = pos
        self.color = color
        self.isKing = False
        self.isDead = False

    def Move(self, map_, pos, players):
        map_.SetCell(self.pos, Blank())
        map_.SetCell(pos, self)
        self.pos = pos

    def Find(self, map_) -> Path:
        dir_s = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        head = map_.paths.Get()
        head.SetPos(self.pos)
        for dir_ in dir_s:
            if self.isKing:
                head.AddNext(self.__FindKing(map_, dir_, self.pos))
            elif (self.color == "white" and dir_[0] == -1) or (self.color == "black" and dir_[0] == 1):
                head.AddNext(self.__FindNormal(map_, dir_, self.pos))
            else:
                head.AddNext(self.__KilledFindNormal(map_, dir_, self.pos))
        return head

    def __FindNormal(self, map_, dir_, pos, killedList=[]) -> Path:
        newPos = (pos[0] + dir_[0], pos[1] + dir_[1])
        cell = map_.GetCell(newPos)
        path = []
        if not cell:
            pass
        elif cell.color == "blank":
            path_ = map_.paths.Get()
            path_.SetPos(newPos)
            path.append(path_)
        elif cell.color != self.color and not cell in killedList:
            newPos = (newPos[0] + dir_[0], newPos[1] + dir_[1])
            landCell = map_.GetCell(newPos)
            if not landCell:
                pass
            elif landCell.color == "blank":
                newKilled = killedList + [cell]
                path_ = map_.paths.Get()
                path_.SetPos(newPos)
                path_.SetKillPiece(cell)
                path.append(path_)
                dir_s = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
                for dir_2 in dir_s:
                    path[0].AddNext(self.__KilledFindNormal(map_, dir_2, newPos, newKilled.copy())) 
        return path

    def __KilledFindNormal(self, map_, dir_, pos, killedList=[]) -> Path:
        newPos = (pos[0] + dir_[0], pos[1] + dir_[1])
        cell = map_.GetCell(newPos)
        path = []
        if not cell or cell.color == "blank":
            pass
        elif cell.color != self.color and not cell in killedList:
            newPos = (newPos[0] + dir_[0], newPos[1] + dir_[1])
            landCell = map_.GetCell(newPos)
            if not landCell:
                pass
            elif landCell.color == "blank":
                newKilled = killedList + [cell]
                path_ = map_.paths.Get()
                path_.SetPos(newPos)
                path_.SetKillPiece(cell)
                path.append(path_)
                dir_s = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
                for dir_2 in dir_s:
                    path[0].AddNext(self.__KilledFindNormal(map_, dir_2, newPos, newKilled.copy())) 
        return path

    def __FindKing(self, map_, dir_, pos, killedList=[]):
        path_s = []
        newPos = pos
        while True:
            newPos = (newPos[0] + dir_[0], newPos[1] + dir_[1])
            cell = map_.GetCell(newPos)
            if not cell:
                break
            elif cell.color == self.color:
                break
            elif cell.color == "blank":
                path = map_.paths.Get()
                path.SetPos(newPos)
                path_s.append(path)
                continue
            elif not cell in killedList:
                newPos = (newPos[0] + dir_[0], newPos[1] + dir_[1])
                landCell = map_.GetCell(newPos)
                if not landCell:
                    break
                elif landCell.color != "blank":
                    break
                else:
                    newKilled = killedList + [cell]
                    path_s = self.__MainDirSearch(map_, dir_, newPos, newKilled.copy())
                    for path in path_s:
                        path.SetKillPiece(cell)
                    break
        return path_s

    def __MainDirSearch(self, map_, dir_, pos, killedList):
        path_s = []
        newPos = pos
        while True:
            path = map_.paths.Get()
            path.SetPos(pos)
            path.AddNext(self.__SideDirSearch(map_, dir_, pos, killedList))
            path_s.append(path)
            newPos = (newPos[0] + dir_[0], newPos[1] + dir_[1])
            cell = map_.GetCell(newPos)
            if not cell:
                break
            elif cell.color == "blank":
                continue
            elif cell.color == self.color:
                break
            elif not cell in killedList:
                newPos = (newPos[0] + dir_[0], newPos[1] + dir_[1])
                landCell = map_.GetCell(newPos)
                if not landCell:
                    break
                elif landCell.color == "blank":
                    newKilled = killedList + [cell]
                    for path in path_s:
                        path.SetKillPiece(cell)
                    laterPath = self.__MainDirSearch(map_, dir_, newPos, newKilled.copy())
                    if laterPath:
                        for path in path_s:
                            path.AddNext(laterPath)
                    break
        return path_s

    def __SideDirSearch(self, map_, dir_, pos_, killedList):
        killedListBranch = killedList.copy()
        newPos = pos_
        path_s = []
        dir_s = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        for dir_2 in dir_s:
            if dir_2[0] * dir_2[1] == dir_[0] * dir_[1]:
                continue
            while True:
                newPos = (newPos[0] + dir_2[0], newPos[1] + dir_2[1])
                cell = map_.GetCell(newPos)
                if not cell:
                    break
                elif cell.color == "blank":
                    continue
                elif cell.color == self.color:
                    break
                elif not cell in killedListBranch:
                    newPos = (newPos[0] + dir_2[0], newPos[1] + dir_2[1])
                    landCell = map_.GetCell(newPos)
                    if not landCell:
                        break
                    elif landCell.color != "blank":
                        break
                    else:
                        killedListBranch.append(cell)
                        path_s = self.__MainDirSearch(map_, dir_2, newPos, killedListBranch)
                        for path in path_s:
                            path.SetKillPiece(cell)
        return path_s

class Blank():
    def __init__(self):
        self.color = "blank"
        self.isDead = True

class Map():
    def __init__(self, WIDTH, HEIGHT, size, Pos2Num, showTurnBottoms):
        self.pos = (WIDTH / 2, HEIGHT / 2)
        self.paths = ObjectPool(Path, size * size)
        self.size = size
        self.__map = {}
        self.turn = "white"
        self.DefaultMapInitializer(Pos2Num)
        self.Pos2Num = Pos2Num
        self.winner = None
        self.showTurnBottoms = showTurnBottoms

    def Reset(self):
        for num in range(1, int(self.size ** 2 / 2 + 1)):
            self.__map[num] = Blank()
        if self.turn != "white":
            self.ChangeTurn()
        self.winner = None
        self.paths.Reset()

    def SetPiece(self, pos, color):
        self.__map[self.Pos2Num(pos)] = Piece(color, pos)

    def RemovePiece(self, pos):
        self.__map[self.Pos2Num(pos)] = Blank()

    def DefaultMapInitializer(self, Pos2Num):
        self.__map = {}
        if self.turn != "white":
            self.ChangeTurn()
        self.winner = None
        self.paths.Reset()
        for row in range(self.size):
            for col in range(self.size):
                if ( row + col ) % 2 == 1:
                    if row < self.size / 2 - 1:
                        self.__map[Pos2Num((row,col))] = Piece("black", (row,col))
                    elif row > self.size / 2:
                        self.__map[Pos2Num((row,col))] = Piece("white", (row,col))
                    else:
                        self.__map[Pos2Num((row,col))] = Blank()

    def GetCell(self, pos):
        if isinstance(pos, int):
            return self.__map.get(pos, None)
        return self.__map.get(self.Pos2Num(pos), None)

    def SetCell(self, pos, item):
        self.__map[self.Pos2Num(pos)] = item

    def JudgeWin(self, players):
        player = players[self.turn]
        if len(player.pieces) == 0:
            self.winner = "white" if player.color == "black" else "black"

    def ChangeTurn(self):
        self.turn = "white" if self.turn == "black" else "black"
        for bottom in self.showTurnBottoms:
            bottom.Push()

    def Refresh(self, players):
        self.ChangeTurn()
        self.paths.Reset()
        players[self.turn].pieces = {}
        for row in range(self.size):
            for col in range(self.size):
                if ( row + col ) % 2 == 1:
                    cell = self.__map[self.Pos2Num((row,col))]
                    if cell and cell.color != "blank":
                        if cell.isDead:
                            self.__map[self.Pos2Num((row,col))] = Blank()
                        elif cell.color == self.turn:
                            players[self.turn].pieces[self.Pos2Num((row,col))] = cell
        players[self.turn].MovementCacheUpdate(self)
        self.JudgeWin(players)

class Player():
    def __init__(self, map_, color):
        self.color = color
        self.pieces = {}
        self.InitPieces(map_)
        self.movementCache = {}
        self.availablePieces = []

    def InitPieces(self, map_):
        self.pieces = {}
        for num in range(1, int(map_.size ** 2 / 2 + 1)):
            cell = map_.GetCell(num)
            if not cell:
                break
            if cell.color == self.color:
                self.pieces[num] = cell

    def ApplyMovement(self, piece, map_):
        piece.Move(map_, piece.pos, self)

    def MovementCacheUpdate(self, map_):
        self.availablePieces = []
        self.movementCache = {}
        maxKillNum = 0
        ###
        print("\n")
        for piece in self.pieces.values():
            path = piece.Find(map_)
            path.SetKillNum()
            self.movementCache[piece] = path
            maxKillNum = max(maxKillNum, path.killNum)
        for piece, path in self.movementCache.items():
            if path.killNum == maxKillNum and path.GetNext():
                self.availablePieces.append(piece)
            ###
            print(path.GetPos(),len(path.GetNext() if path.GetNext() else []), path.killNum)

class Bottom():
    def __init__(self, pos=(0,0), size=(0,0), text="", textSize=32, colors=["#000000", "#ffffff"]):
        self.pos = pos
        self.size = size
        self.text = text
        self.colors = colors
        self.textSurf = pygame.font.Font(None, textSize).render(text, True, self.colors[0])
        self.textRect = self.textSurf.get_rect(center = (self.size[0] / 2, self.size[1] / 2))
        self.surf = pygame.Surface(self.size)
        self.rect = self.surf.get_rect(center = self.pos)
        self.__isActive = False

    def Push(self):
        self.__isActive = False if self.__isActive else True

    def IsActive(self):
        return self.__isActive

    def Render(self):
        if self.__isActive:
            pygame.draw.rect(self.surf, self.colors[0], (0, 0, self.size[0], self.size[1]), 0)
            pygame.draw.rect(self.surf, self.colors[1], (2, 2, self.size[0] - 4, self.size[1] - 4), 0)
            self.surf.blit(self.textSurf, self.textRect)
        else:
            pygame.draw.rect(self.surf, self.colors[1], (0, 0, self.size[0], self.size[1]), 0)
            pygame.draw.rect(self.surf, self.colors[0], (2, 2, self.size[0] - 4, self.size[1] - 4), 0)
        return self.surf

class Game():
    def __init__(self):
        self.WIDTH = WIDTH
        self.HEIGHT = HEIGHT
        self.screen = pygame.display.set_mode((self.WIDTH,self.HEIGHT))
        self.font1 = pygame.font.Font(None, 128)
        self.mapSize = MAP_SIZE
        self.cellSize = CELL_SIZE
        self.pieceSize = PIECE_SIZE
        self.numMap = {}
        self.InitNumMap()

        self.showTurnBottoms = []
        self.showTurnBottoms.append(Bottom(pos=(self.WIDTH / 4 * 1, self.HEIGHT / 18), size=(self.WIDTH / 5, 50), text="WHITE TURN", colors=["#000000", "#ffffff"]))
        self.showTurnBottoms.append(Bottom(pos=(self.WIDTH / 4 * 3, self.HEIGHT / 18), size=(self.WIDTH / 5, 50), text="BLACK TURN", colors=["#ffffff", "#000000"]))
        self.showTurnBottoms[0].Push()

        self.map = Map(self.WIDTH, self.HEIGHT, self.mapSize, self.Pos2Num, self.showTurnBottoms)
        self.players = {"white": Player(self.map, "white"), "black": Player(self.map, "black")}
        self.players["white"].MovementCacheUpdate(self.map)
        self.availablePos = []
        self.availablePaths = []
        self.isJumping = False
        self.selected = None

        self.editModeBottom = Bottom(pos=(40,self.HEIGHT / 7 * 1),size=(60,50),text="EDIT")
        self.resetBottom = Bottom(pos=(40,self.HEIGHT / 7 * 2),size=(60,50),text="RESET", textSize=24)
        self.defaultGameBottom = Bottom(pos=(40,self.HEIGHT / 7 * 3),size=(60,50),text="GAME", textSize=26)
        self.resetBottom.Push()
        self.defaultGameBottom.Push()

    def PieceEditor(self, pos_, getPressed):
        pos = self.InputPos(pos_)
        if getPressed[0] and getPressed[2]:
            return
        if getPressed[0]:
            color = "white"
        elif getPressed[2]:
            color = "black"
        elif getPressed[1]:
            color = "king"
        if pos in self.numMap.keys():
            cell = self.map.GetCell(pos)
            if not cell:
                return
            if cell.color != "blank":
                if color == "king":
                    cell.isKing = not cell.isKing
                elif cell.color == color:
                    self.map.RemovePiece(pos)
                else:
                    self.map.SetPiece(pos, color)
            else:
                self.map.SetPiece(pos, color)

    def InitNumMap(self):
        num = 1
        for row in range(self.mapSize):
            for col in range(self.mapSize):
                if (row + col) % 2 == 1:
                    self.numMap[(row,col)] = num
                    num += 1

    def Pos2Num(self, pos):
        return self.numMap.get(pos,None)

    def InputPos(self, inputPos) -> tuple:
        return (int((inputPos[1] - self.map.pos[1]) // self.cellSize + self.mapSize / 2), int((inputPos[0] - self.map.pos[0]) // self.cellSize + self.mapSize / 2))

    def JudgeMovment(self, pos_):
        pos = self.InputPos(pos_)
        cell = self.map.GetCell(pos)
        if not cell:
            return
        elif cell.color != "blank":
            if self.selected and self.isJumping:
                return
            self.selected = cell if self.selected != cell and self.map.turn == cell.color and cell in self.players[self.map.turn].availablePieces else None
            self.availablePos = []
            if self.selected == None:
                return
            self.availablePos.append(pos)
            for path in self.players[cell.color].movementCache[cell].GetNext():
                self.availablePaths.append(path)
                self.availablePos.append(path.GetPos())
        else:
            if pos in self.availablePos and self.selected:
                self.availablePos = []
                for path in self.availablePaths:
                    if path.GetPos() == pos:
                        self.availablePaths = []
                        self.selected.Move(self.map, pos, self.players)
                        capturedPiece = path.GetKillPiece()
                        if capturedPiece != None:
                            capturedPiece.isDead = True
                        nextPaths = path.GetNext()
                        if not nextPaths:
                            self.map.Refresh(self.players)
                            if (self.selected.pos[0] == 0 and self.selected.color == "white") or (self.selected.pos[0] == self.map.size - 1 and self.selected.color == "black"):
                                self.selected.isKing = True
                            self.isJumping = False
                            self.selected = None
                        else:
                            for path in nextPaths:
                                self.availablePaths.append(path)
                                self.availablePos.append(path.GetPos())
                                self.isJumping = True
                        break

    def Render(self):
        self.screen.fill("#d49349")
        for row in range(self.mapSize):
            for col in range(self.mapSize):
                cellPos = (self.map.pos[0] - (self.mapSize / 2 - col) * self.cellSize, self.map.pos[1] - (self.mapSize / 2 - row) * self.cellSize)
                pygame.draw.rect(self.screen, "#e6e6e6" if ( row + col ) % 2 == 0 else "black", (cellPos[0], cellPos[1], self.cellSize, self.cellSize), 0)
                if ( row + col ) % 2 == 1:
                    if (row,col) in self.availablePos:
                        pygame.draw.rect(self.screen, "#4fa5f0", (cellPos[0], cellPos[1], self.cellSize, self.cellSize), 4)
                    cell = self.map.GetCell((row,col))
                    if isinstance(cell, Piece):
                        pygame.draw.circle(self.screen, "#e53636" if cell.color == "black" else "#f1f1f1", (cellPos[0] + self.cellSize / 2, cellPos[1] + self.cellSize / 2), self.pieceSize / 2, 0)
                        if cell.isKing:
                            pygame.draw.circle(self.screen, "#f1f1f1" if cell.color == "black" else "#e53636", (cellPos[0] + self.cellSize / 2, cellPos[1] + self.cellSize / 2), self.pieceSize / 4, 0)
        if self.map.winner != None:
            textSurf = self.font1.render("Winner:"+self.map.winner,True,"#e3b24f")
            textRect = textSurf.get_rect(center = self.map.pos)
            self.screen.blit(textSurf,textRect)

        self.screen.blit(self.editModeBottom.Render(), self.editModeBottom.rect)
        if self.editModeBottom.IsActive():
            self.screen.blit(self.resetBottom.Render(),self.resetBottom.rect)
            self.screen.blit(self.defaultGameBottom.Render(),self.defaultGameBottom.rect)
        for bottom in self.showTurnBottoms:
            self.screen.blit(bottom.Render(), bottom.rect)
    
game = Game()
pygame.display.set_caption("Draughts")
clock = pygame.time.Clock()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        if event.type == pygame.MOUSEBUTTONDOWN:

            if game.editModeBottom.IsActive() and game.resetBottom.rect.collidepoint(event.pos):
                game.map.Reset()
            if game.editModeBottom.IsActive() and game.defaultGameBottom.rect.collidepoint(event.pos):
                game.map.DefaultMapInitializer(game.Pos2Num)

            if game.editModeBottom.rect.collidepoint(event.pos):
                game.editModeBottom.Push()
                if not game.editModeBottom.IsActive():
                    game.players["white"].InitPieces(game.map)
                    game.players["black"].InitPieces(game.map)
                    game.players["white"].MovementCacheUpdate(game.map)
                    game.players["black"].MovementCacheUpdate(game.map)

            if game.editModeBottom.IsActive():
                game.PieceEditor(pygame.mouse.get_pos(), pygame.mouse.get_pressed())
                if game.showTurnBottoms[0].rect.collidepoint(event.pos) or game.showTurnBottoms[1].rect.collidepoint(event.pos):
                    game.map.ChangeTurn()
            else:
                game.JudgeMovment(pygame.mouse.get_pos())

    game.Render()
    pygame.display.update()
    clock.tick(60)