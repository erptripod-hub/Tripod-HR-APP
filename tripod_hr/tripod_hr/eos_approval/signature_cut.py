# Copyright (c) 2026, Tripod Mena
# Cut the employee signature out of a scanned, signed EOS print (PDF or image).
# Pure Pillow + PyPDF2 (both ship with Frappe) - no extra dependencies.
#
# Layout assumption (EOS UAE / EOS KSA print formats): one long signature line
# with 4 equal columns under it; the employee signs above column 1.

import io
import re

from PIL import Image

DARK = 110          # printed line threshold
INK_SAT = 55        # coloured pen: channel spread
INK_GRAY = 185      # coloured pen: max brightness
BLACK_INK = 150     # black pen threshold (above the line only)


def load_page(content, is_pdf):
	if not is_pdf:
		return Image.open(io.BytesIO(content)).convert("RGB")
	import PyPDF2

	reader = PyPDF2.PdfReader(io.BytesIO(content))
	page = reader.pages[-1]  # signatures are on the last page
	xobjects = page["/Resources"]["/XObject"].get_object()
	best = None
	for key in xobjects:
		obj = xobjects[key].get_object()
		if obj.get("/Subtype") != "/Image" or obj.get("/Filter") not in ("/DCTDecode", ["/DCTDecode"]):
			continue
		area = int(obj["/Width"]) * int(obj["/Height"])
		if not best or area > best[0]:
			best = (area, key, obj)
	if not best:
		return None
	img = Image.open(io.BytesIO(best[2]._data)).convert("RGB")

	# Apply the page rotation used to place the scan ("a b c d e f cm /Name Do")
	stream = page.get_contents().get_data().decode("latin-1")
	m = re.search(
		r"([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+[-\d.]+\s+[-\d.]+\s+cm\s*" + re.escape(best[1]) + r"\s+Do",
		stream,
	)
	if m:
		a, b, c, d = (float(x) for x in m.groups())
		if abs(a) < 1e-6 and abs(d) < 1e-6:
			if b < 0 < c:
				img = img.transpose(Image.ROTATE_270)
			elif c < 0 < b:
				img = img.transpose(Image.ROTATE_90)
		elif a < 0 and d < 0:
			img = img.transpose(Image.ROTATE_180)
	return img


def _find_signature_line(gray):
	w, h = gray.size
	lut = [255 if v < DARK else 0 for v in range(256)]
	dark = gray.point(lut)
	rows = []
	for y in range(int(h * 0.15), h):
		row = dark.crop((0, y, w, y + 1))
		box = row.getbbox()
		if not box:
			continue
		span = box[2] - box[0]
		count = row.histogram()[255]
		if span > w * 0.7 and count > span * 0.85:
			rows.append((y, box[0], box[2]))
	if not rows:
		return None
	groups, cur = [], [rows[0]]
	for r in rows[1:]:
		if r[0] - cur[-1][0] <= 2:
			cur.append(r)
		else:
			groups.append(cur)
			cur = [r]
	groups.append(cur)
	thin = [g for g in groups if len(g) <= 8]  # filled header bars are much taller
	if not thin:
		return None
	g = thin[-1]  # the signature line is the last thin full-width line
	return g[0][0], g[-1][0], min(r[1] for r in g), max(r[2] for r in g)


def cut_employee_signature(img):
	"""Return PNG bytes of the employee signature (transparent background) or None."""
	gray = img.convert("L")
	line = _find_signature_line(gray)
	if not line:
		return None
	ly0, ly1, lx0, lx1 = line
	H = img.size[1]
	colw = (lx1 - lx0) / 4.0
	top, bottom = max(ly0 - int(H * 0.06), 0), min(ly1 + int(H * 0.03), H)
	right = int(lx0 + colw * 1.4)
	band = img.crop((lx0, top, right, bottom))
	bw, bh = band.size
	px = list(band.getdata())

	coloured = [((max(p) - min(p)) > INK_SAT and sum(p) / 3 < INK_GRAY) for p in px]
	if sum(coloured) > 300:
		mask = coloured
	else:  # black pen: only above the printed line
		limit = (ly0 - top - 3) * bw
		mask = [(i < limit and sum(p) / 3 < BLACK_INK) for i, p in enumerate(px)]

	# remove the printed line rows and isolated scanner specks
	lt, lb = max(ly0 - top - 4, 0), ly1 - top + 5
	for y in range(lt, min(lb, bh)):
		for x in range(bw):
			mask[y * bw + x] = False
	clean = [False] * len(mask)
	for y in range(1, bh - 1):
		base = y * bw
		for x in range(1, bw - 1):
			if not mask[base + x]:
				continue
			n = 0
			for dy in (-bw, 0, bw):
				for dx in (-1, 0, 1):
					n += mask[base + x + dy + dx]
			clean[base + x] = n >= 4
	mask = clean

	# split from the HR column at the widest gap near the column boundary
	inkx = sorted({i % bw for i, v in enumerate(mask) if v})
	if len(inkx) < 10:
		return None
	lo, hi = colw * 0.6, colw * 1.4
	near = [x for x in inkx if lo <= x <= hi]
	split = int(colw)
	if len(near) > 1:
		gaps = [(near[i + 1] - near[i], i) for i in range(len(near) - 1)]
		gap, i = max(gaps)
		if gap > 3:
			split = (near[i] + near[i + 1]) // 2
	xs = [x for x in inkx if x < split]
	if len(xs) < 10:
		return None
	x0, x1 = xs[0], xs[-1] + 1
	ys = [i // bw for i, v in enumerate(mask) if v and x0 <= i % bw < x1]
	y0, y1 = min(ys), max(ys) + 1
	pad = 6
	x0, y0 = max(x0 - pad, 0), max(y0 - pad, 0)
	x1, y1 = min(x1 + pad, split), min(y1 + pad, bh)

	out = Image.new("RGBA", (x1 - x0, y1 - y0), (0, 0, 0, 0))
	opx = out.load()
	for y in range(y0, y1):
		for x in range(x0, x1):
			if mask[y * bw + x]:
				r, g, b = px[y * bw + x]
				opx[x - x0, y - y0] = (r, g, b, 255)
	buf = io.BytesIO()
	out.save(buf, "PNG")
	return buf.getvalue()
