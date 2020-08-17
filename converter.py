# TODO
# - Use hidetchi pieces then adjust mochigoma positioning
# - Make gif size smaller (search imageio)
# - Make rendered gifs public in django
# - Push to heroku
import re
import datetime
import argparse
import os
import cjkwrap

import shogi.KIF
import imageio
from PIL import Image, ImageDraw, ImageFont
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

FONT_SIZE_NAME = 16
FONT_SIZE_META = 12

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

SENTE_NAME_COORD = add_c(SENTE_MOCHI_COORD, (0, -AIR_MARGIN[1] * 2 - FONT_SIZE_NAME))
GOTE_NAME_COORD = add_c(GOTE_MOCHI_COORD, (0, MOCHI_SIZE[1]))
def TEXT_SPACING(font_size):
    return font_size * 1.15
def TEXT_CHARS_PER_LINE(font_size):
    return int(MOCHI_SIZE[0] / (font_size / 2))

TRANSPARENT_SQUARE_COLOR = (255, 160, 120, 120)

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

meta_regexes = [
        ['Start date', r'開始日時：(.*)'],
        ['End date', r'終了日時：(.*)'],
        ['Location', r'場所：(.*)'],
        ['Time control', r'持ち時間：(.*)'],
    ]

replacements = [
        ['秒', 's'],
        ['分', 'm'],
        ['時', 'h']
    ]

# fix wrap not treating \n as break
def wrap_fix(s, n):
    return '\n'.join(cjkwrap.wrap(s, n, replace_whitespace=False)).split('\n')


def kif2gif(input_kif, gif_dirname='', gif_filename='', start=0, end=999999, delay=1, start_delay=5, final_delay=5):
    if start > end:
        raise ValueError
    kif = shogi.KIF.Parser.parse_str(re.sub(' +', ' ', input_kif))[0]
    meta_regex_search = [[meta_regex[0], re.search(meta_regex[1], input_kif)] for meta_regex in meta_regexes]
    kif['meta'] = [meta[0] + ': ' + meta[1][1] for meta in meta_regex_search if meta[1]]
    for i in range(len(kif['meta'])):
        for replacement in replacements:
            kif['meta'][i] = kif['meta'][i].replace(replacement[0], replacement[1])

    # draw initial board
    empty_board = Image.new('RGBA', IMAGE_SIZE, '#EECA7E')
    ban = Image.open('assets/ban.png')
    #grid = Image.open('assets/grid.png')
    mochi = Image.open('assets/dai.png')
    empty_board.paste(ban, BOARD_COORD, ban)
    #empty_board.paste(grid, BOARD_COORD, grid)
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

    font_name = ImageFont.truetype("assets/NotoSansMonoCJKjp-Regular.otf", FONT_SIZE_NAME)
    font_meta = ImageFont.truetype("assets/NotoSansMonoCJKjp-Regular.otf", FONT_SIZE_META)

    board = shogi.Board()
    imgs = []
    num_moves = 0

    if start <= num_moves and num_moves <= end:
        img = render_position(str(board), empty_board.copy(), kif, font_name, font_meta)
        imgs.append(array(img))
    num_moves += 1

    print('Turning positions to pngs...')
    for move in kif['moves']:
        #print(move)
        board.push_usi(move)
        #print(board)
        if start <= num_moves and num_moves <= end:
            img = render_position(str(board), empty_board.copy(), kif, font_name, font_meta, move)
            imgs.append(array(img))
        num_moves += 1
    if not gif_filename:
        gif_filename = str(datetime.datetime.now()).replace(' ', '_').replace(':', '-').replace('.', '-') + '.gif'
    gif_path = os.path.join(gif_dirname, gif_filename)

    if len(imgs) > 1:
        duration_list = [start_delay] + [delay] * (len(imgs) - 2) + [final_delay]
    else:
        duration_list = [1]

    print('Compiling pngs to gif...')
    imageio.mimsave(gif_path, imgs, duration=duration_list, subrectangles=True)
    print('Optimizing gif filesize...')
    optimize(gif_path)
    return gif_path



def render_position(pos, board, kif, font_name, font_meta, move=None):
    rows = pos.split('\n')

    # render bangoma
    move_coords = []
    if move:
        move_split = [move[:2], move[2:]]
        for move_coord in move_split:
            if '*' not in move_coord:
                move_coords.append((9 - int(move_coord[0]), ord(move_coord[1]) - ord('a')))
            else:
                move_coords.append(move_coord[0].lower())

    transparent_square = Image.new('RGBA', SQUARE_SIZE, TRANSPARENT_SQUARE_COLOR)

    for p_y in range(9):
        row = rows[p_y]
        row_pieces = [row[i:i+3] for i in range(0, len(row), 3)]
        for p_x in range(9):
            piece_image = pieces_dict[row_pieces[p_x].strip()]
            piece_offset = mul_c((p_x, p_y), SQUARE_SIZE)
            coord = add_c(CORNER_COORD, piece_offset)
            if (p_x, p_y) in move_coords:
                board.paste(transparent_square, coord, transparent_square)
            if piece_image:
                board.paste(piece_image, coord, piece_image)

    grid = Image.open('assets/grid.png')
    board.paste(grid, BOARD_COORD, grid)

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

    # render text
    draw = ImageDraw.Draw(board)
    sente_text = '|(' + kif['names'][0]
    sente_text_wrapped = wrap_fix(sente_text, TEXT_CHARS_PER_LINE(FONT_SIZE_NAME))
    sente_text_wrapped[0] = sente_text_wrapped[0].replace('|(', '☗')

    for i, text_line in enumerate(sente_text_wrapped):
        draw.text(add_c(SENTE_NAME_COORD, (0, TEXT_SPACING(FONT_SIZE_NAME) * (i - len(sente_text_wrapped) + 1))), text_line, '#000', font=font_name)

    gote_text = '|(' + kif['names'][1]

    gote_text_wrapped = wrap_fix(gote_text, TEXT_CHARS_PER_LINE(FONT_SIZE_NAME))
    gote_text_wrapped[0] = gote_text_wrapped[0].replace('|(', '☖')
    coord = GOTE_NAME_COORD
    for text_line in gote_text_wrapped:
        draw.text(coord, text_line, '#000', font=font_name)
        coord = add_c(coord, (0, TEXT_SPACING(FONT_SIZE_NAME)))

    meta_with_newlines = ['', '', ''] + kif['meta']
    meta_text_wrapped = sum([wrap_fix(meta_field, TEXT_CHARS_PER_LINE(FONT_SIZE_META)) for meta_field in meta_with_newlines], [])
    for text_line in meta_text_wrapped:
        draw.text(coord, text_line, '#000', font=font_meta)
        coord = add_c(coord, (0, TEXT_SPACING(FONT_SIZE_META)))


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
