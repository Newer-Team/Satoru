// _cAlgorithms.cpp : Includes C implementations of several bottleneck functions, for speed.
// decodeRGBA8 is from Wii U GTX Extractor by Treeki (https://github.com/Treeki/RandomStuff)
// DXT functions are from libtxc_dxtn, and Wii U GTX Extractor.
// compress is written from scratch by Kinnay.
// decompress is from Wiimms SZS Tools.


#include "stdafx.h"
#include "stdio.h"

#define Export __declspec(dllexport)

typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;

extern "C" Export char * decodeRGBA8(unsigned int w, unsigned int h, char * data) {
    char * output = new char[w * h * 4];
    for (unsigned int y = 0; y < h; y++) {
        for (unsigned int x = 0; x < w; x++) {
            unsigned int pos = (y & ~15) * w;
            pos ^= x & 3;
            pos ^= (x & 0b100) << 1;
            pos ^= (x & 0b1000) << 3;
            pos ^= (x & ~0x7) << 4;
            pos ^= (y & 0xE) << 3;
            pos ^= (y & 0x10) << 4;
            pos ^= (y & 0x21) << 2;
            pos *= 4;

            unsigned int dest = (y * w + x) * 4;
            char * s = data + pos;
            *(output + dest) = *s;
            *(output + dest + 1) = *(s + 1);
            *(output + dest + 2) = *(s + 2);
            *(output + dest + 3) = *(s + 3);
        }
    }
    return output;
}

u32 DXTToRGB(u8 * pointer, u32 i, u32 j) {
    u16 color0 = *(u16 *)(pointer);
    u16 color1 = *(u16 *)(pointer + 2);
    u32 bits = *(u32 *)(pointer + 4);
    u32 bitpos = 2 * (j * 4 + i);
    u8 code = (bits >> bitpos) & 3;
    u8 r0exp = (color0 >> 11) * 0xFF / 0x1F;
    u8 g0exp = ((color0 >> 5) & 0x3F) * 0xFF / 0x3F;
    u8 b0exp = (color0 & 0x1F) * 0xFF / 0x1F;
    u8 r1exp = (color1 >> 11) * 0xFF / 0x1F;
    u8 g1exp = ((color1 >> 5) & 0x3F) * 0xFF / 0x3F;
    u8 b1exp = (color1 & 0x1F) * 0xFF / 0x1F;

    if (code == 0) {
        return (b0exp << 16) | (g0exp << 8) | r0exp;
    }
    else if (code == 1) {
        return (b1exp << 16) | (g1exp << 8) | r1exp;
    }
    else if (code == 2) {
        return (((b0exp * 2 + b1exp) / 3) << 16) | (((g0exp * 2 + g1exp) / 3) << 8) | ((r0exp * 2 + r1exp) / 3);
    }
    else {
        return (((b0exp + b1exp * 2) / 3) << 16) | (((g0exp + g1exp * 2) / 3) << 8) | ((r0exp + r1exp * 2) / 3);
    }

}

char * DXT5ToRGBA(u32 w, u8 * data, u32 i, u32 j) {
    u8 * pointer = data + ((w + 3) / 4 * (j / 4) + (i / 4)) * 16;
    u8 alpha0 = pointer[0];
    u8 alpha1 = pointer[1];

    u8 bitpos = ((j & 3) * 4 + (i & 3)) * 3;
    u8 acodelow = pointer[2 + bitpos / 8];
    u8 acodehigh = pointer[3 + bitpos / 8];
    u8 code = (acodelow >> (bitpos & 7) | (acodehigh << (8 - (bitpos & 7)))) & 7;
    u32 argb = DXTToRGB(pointer + 8, i & 3, j & 3);

    u8 a = 255;
    if (code == 0) { a = alpha0; }
    else if (code == 1) { a = alpha1; }
    else if (alpha0 > alpha1) {
        a = (alpha0 * (8 - code) + (alpha1 * (code - 1))) / 7;
    }
    else if (code < 6) {
        a = (alpha0 * (6 - code) + (alpha1 * (code - 1))) / 5;
    }
    else if (code == 6) {
        a = 0;
    }
    argb |= a << 24;
    return (char *)&argb;
}

extern "C" Export char * decodeDXT5(int w, int h, char * data) {
    u8 * work = new u8[w * h];
    int bw = w / 4;
    int bh = h / 4;
    for (int y = 0; y < bh; y++) {
        for (int x = 0; x < bw; x++) {
            int pos = ((y >> 4) * bw * 16) & 0xFFFF;
            pos ^= (y & 1);
            pos ^= (x & 0xF) << 1;
            pos ^= (x & 0x18) << 2;
            pos ^= (x & ~0x1F) << 4;
            pos ^= (y & 6) << 6;
            pos ^= (y & 8) << 1;
            pos ^= (y & 0x10) << 2;
            pos ^= (y & 0x20);

            int dest = (y * bw + x) * 16;
            pos *= 16;
            memcpy(work + dest, data + pos, 16);
        }
    }

    u8 * output = new u8[w * h * 4];
    for (int y = 0; y < h; y++) {
        for (int x = 0; x < w; x++) {
            char * outval = DXT5ToRGBA(w, work, x, y);
            u32 dest = (y * w + x) * 4;
            memcpy(output+dest, outval, 4);
        }
    }

    return (char *)output;
}

extern "C" Export u8 * compress(u8 * data, u32 size) {
    u8 * end = data + size;
    u8 * out = new u8[size + (size+8)/8];
    u8 * fake = out;
    u8 n = 8;
    while (data < end) {
        if (n == 8) {
            n = 0;
            *fake++ = 0xFF;
        }
        *fake++ = *data++;
        n++;
    }
    return out;
}

extern "C" Export u8 * decompress(u8 * data) {
    u32 outsize = ((*(data + 4)) << 24) | ((*(data + 5)) << 16) | ((*(data + 6)) << 8) | *(data + 7);
    u8 * out = new u8[outsize];
    u8 * result = out;
    u8 * end = out + outsize;
    u8 bits = 0;
    u8 code = 0;
    data += 16;
    while (out < end) {
        if (bits == 0) {
            code = *data++;
            bits = 8;
        }
        if ((code & 0x80) != 0) {
            *out++ = *data++;
        }
        else {
            u8 b1 = *data++;
            u8 b2 = *data++;
            u8 * copy = out - ((b1 & 0xF) << 8 | b2) - 1;
            int n = b1 >> 4;
            if (n == 0) {
                n = *data++ + 0x12;
            }
            else {
                n += 2;
            }
            while (n --> 0) {
                *out++ = *copy++;
            }
        }
        code <<= 1;
        bits--;
    }
    return result;
}
