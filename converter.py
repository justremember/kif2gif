# TODO
# - Use hidetchi pieces then adjust mochigoma positioning
# - Make gif size smaller (search imageio)
# - Make rendered gifs public in django
# - Push to heroku
import re
import datetime
import argparse
import os

import shogi.KIF
import imageio
from PIL import Image, ImageDraw
from numpy import array
from pygifsicle import optimize

DEFAULT_GIF_PATH = 'output.gif'

def add_c(*c):
    d = [0, 0]
    for i in c:
        d[0] += i[0]
        d[1] += i[1]
    return tuple(d)
def mul_c(c1, x):
    if type(x) == list or type(x) == tuple:
        return (c1[0] * x[0], c1[1] * x[1])
    else:
        return (c1[0] * x, c1[1] * x)
def neg_c(c):
    return (-c[0], -c[1])
def sub_c(c1, c2):
    return (c1[0] - c2[0], c1[1] - c2[1])

BOARD_SIZE = (410, 454) # dependent on the board image
BOARD_MARGIN = (11, 11) # dependent on the board image
SQUARE_SIZE = (43, 48) # dependent on the piece image
PIECE_SIZE = SQUARE_SIZE # dependent on the piece image
AIR_MARGIN = (4, 4) # arbitrary

MOCHI_SIZE = (170, 200) # dependent on the mochi image
MOCHI_MARGIN = (0, 4) # arbitrary

IMAGE_SIZE = (BOARD_SIZE[0] + MOCHI_SIZE[0] * 2 + AIR_MARGIN[0] * 4, BOARD_SIZE[1] + AIR_MARGIN[1] * 2)
BOARD_COORD = (MOCHI_SIZE[0] + AIR_MARGIN[0] * 2, AIR_MARGIN[1])
CORNER_COORD = add_c(BOARD_COORD, BOARD_MARGIN)

GOTE_MOCHI_COORD = AIR_MARGIN
SENTE_MOCHI_COORD = add_c(AIR_MARGIN,
        BOARD_SIZE,
        (MOCHI_SIZE[0] + AIR_MARGIN[0] * 2, -MOCHI_SIZE[1]))
GOTE_MOCHI_PIECE_COORD = add_c(GOTE_MOCHI_COORD, MOCHI_MARGIN)
SENTE_MOCHI_PIECE_COORD = add_c(SENTE_MOCHI_COORD, MOCHI_MARGIN)
MOCHI_PIECE_DIST = (MOCHI_SIZE[0] // 2, SQUARE_SIZE[1])

mochi_offsets = {
        'p': (0, 3), 'l': (1, 2), 'n': (0, 2), 's': (1, 1), 'g': (0, 1), 'b': (1, 0), 'r': (0, 0)
}

ident_mochi_offsets = {
        'p': [(0, 30), (6, 20), (8, 10), (12, 7)],
        'l': [(0, 33), (3, 20), (4, 15)],
        'n': [(0, 33), (3, 20), (4, 15)],
        's': [(0, 35), (3, 20), (4, 15)],
        'g': [(0, 35), (3, 20), (4, 15)],
        'b': [(0, 38)],
        'r': [(0, 38)]
}

pieces_dict = {
        '.': None,
        'p': Image.open('pieces_ryoko1/Gfu.png'),
        'l': Image.open('pieces_ryoko1/Gkyo.png'),
        'n': Image.open('pieces_ryoko1/Gkei.png'),
        's': Image.open('pieces_ryoko1/Ggin.png'),
        'g': Image.open('pieces_ryoko1/Gkin.png'),
        'k': Image.open('pieces_ryoko1/Gou.png'),
        'r': Image.open('pieces_ryoko1/Ghi.png'),
        'b': Image.open('pieces_ryoko1/Gkaku.png'),
        '+p': Image.open('pieces_ryoko1/Gto.png'),
        '+l': Image.open('pieces_ryoko1/Gnkyo.png'),
        '+n': Image.open('pieces_ryoko1/Gnkei.png'),
        '+s': Image.open('pieces_ryoko1/Gngin.png'),
        '+r': Image.open('pieces_ryoko1/Gryu.png'),
        '+b': Image.open('pieces_ryoko1/Guma.png'),
        'P': Image.open('pieces_ryoko1/Sfu.png'),
        'L': Image.open('pieces_ryoko1/Skyo.png'),
        'N': Image.open('pieces_ryoko1/Skei.png'),
        'S': Image.open('pieces_ryoko1/Sgin.png'),
        'G': Image.open('pieces_ryoko1/Skin.png'),
        'K': Image.open('pieces_ryoko1/Sou.png'),
        'R': Image.open('pieces_ryoko1/Shi.png'),
        'B': Image.open('pieces_ryoko1/Skaku.png'),
        '+P': Image.open('pieces_ryoko1/Sto.png'),
        '+L': Image.open('pieces_ryoko1/Snkyo.png'),
        '+N': Image.open('pieces_ryoko1/Snkei.png'),
        '+S': Image.open('pieces_ryoko1/Sngin.png'),
        '+R': Image.open('pieces_ryoko1/Sryu.png'),
        '+B': Image.open('pieces_ryoko1/Suma.png'),
    }


def kif2gif(input_kif, gif_dirname='', gif_filename='', start=0, end=999999, delay=1):
    if start > end:
        raise ValueError
    kif = shogi.KIF.Parser.parse_str(re.sub(' +', ' ', input_kif))

    # draw initial board
    empty_board = Image.new('RGBA', IMAGE_SIZE, '#EECA7E')
    ban = Image.open('assets/ban.png')
    grid = Image.open('assets/grid.png')
    mochi = Image.open('assets/dai.png')
    empty_board.paste(ban, BOARD_COORD, ban)
    empty_board.paste(grid, BOARD_COORD, grid)
    empty_board.paste(mochi, SENTE_MOCHI_COORD, mochi)
    empty_board.paste(mochi, GOTE_MOCHI_COORD, mochi)
    """
    draw = ImageDraw.Draw(initial_board)
    for i in range(10):
        line_start = (SQUARE_SIZE[0] * i + BOARD_MARGIN[0], 0)
        line_end = add_c(line_start, (0, BOARD_SIZE[1]))
        draw.line(add_c(line_start, BOARD_COORD) + add_c(line_end, BOARD_COORD), fill="#ffffff")

        line_start = (0, SQUARE_SIZE[1] * i + BOARD_MARGIN[1])
        line_end = add_c(line_start, (BOARD_SIZE[0], 0))
        draw.line(add_c(line_start, BOARD_COORD) + add_c(line_end, BOARD_COORD), fill="#ffffff")
    """

    board = shogi.Board()
    imgs = []
    num_moves = 0
    
    if start <= num_moves and num_moves <= end:
        img = render_position(str(board), empty_board.copy())
        imgs.append(array(img))
    num_moves += 1

    for move in kif[0]['moves']:
        #print(move)
        board.push_usi(move)
        #print(board)
        if start <= num_moves and num_moves <= end:
            img = render_position(str(board), empty_board.copy())
            imgs.append(array(img))
        num_moves += 1
    if not gif_filename:
        gif_filename = str(datetime.datetime.now()).replace(' ', '_').replace(':', '-').replace('.', '-') + '.gif'
    gif_path = os.path.join(gif_dirname, gif_filename)
    last_delay = 5
    if last_delay < delay:
        last_delay = delay
    imageio.mimsave(gif_path, imgs, duration=[delay] * (len(imgs) - 1) + [last_delay], subrectangles=True)
    optimize(gif_path)
    return gif_path



def render_position(pos, board):
    rows = pos.split('\n')

    # render bangoma
    for p_y in range(9):
        row = rows[p_y]
        row_pieces = [row[i:i+3] for i in range(0, len(row), 3)]
        for p_x in range(9):
            piece_image = pieces_dict[row_pieces[p_x].strip()]
            if piece_image:
                piece_offset = mul_c((p_x, p_y), SQUARE_SIZE)
                coord = add_c(CORNER_COORD, piece_offset)
                board.paste(piece_image, coord, piece_image)

    # render mochigoma
    if len(rows) > 9:
        for mochigoma in rows[-1].strip().split(' '):
            koma, num = mochigoma.split('*')
            num = int(num)
            mochi_offset = mochi_offsets[koma.lower()]

            if koma.islower():
                init_coord = GOTE_MOCHI_PIECE_COORD
            else:
                init_coord = SENTE_MOCHI_PIECE_COORD
            coord = add_c(init_coord, mul_c(MOCHI_PIECE_DIST, mochi_offset))

            ident_mochi_offset = 10
            for i in ident_mochi_offsets[koma.lower()]:
                if num < i[0]: break
                ident_mochi_offset = i[1]

            piece_image = pieces_dict[koma]
            for i in range(num):
                board.paste(piece_image,
                        add_c(coord, (ident_mochi_offset * i, 0)),
                        piece_image)

    return board

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument(
        'path', nargs='*', help='Path to the kif file/folder')
    parser.add_argument(
        '-d', '--delay', help='Delay between moves in seconds', default=1)
    parser.add_argument(
        '-o', '--out', help='Name of the output folder', default=os.getcwd())
    parser.add_argument(
        '-s', '--start', help='Starting move # (inclusive)', default=0)
    parser.add_argument(
        '-e', '--end', help='End move # (inclusive)', default=9999)
    args = parser.parse_args()

    if not args.path:
        print('Please type path of kif files')

    for path in args.path:
        if os.path.isfile(path):
            input_str = open(path, 'r').read()
            kif2gif(input_str, delay=float(args.delay), start=int(args.start), end=int(args.end), gif_dirname=args.out)


if __name__ == '__main__':
    main()
