import re

path = "c:/Users/shrij/Downloads/sparc_vercel_bundler/startup_shield_web/app.js"

with open(path, "rb") as f:
    raw = f.read()
if raw[:3] == b"\xef\xbb\xbf":
    raw = raw[3:]
content = raw.decode("utf-8")

def fix_mojibake(s):
    out = []
    buf = bytearray()
    for ch in s:
        cp = ord(ch)
        if cp < 128:
            if buf:
                try:
                    out.append(buf.decode("utf-8"))
                except Exception:
                    out.append(buf.decode("cp1252", errors="replace"))
                buf.clear()
            out.append(ch)
        else:
            try:
                buf.extend(ch.encode("cp1252"))
            except Exception:
                if buf:
                    try:
                        out.append(buf.decode("utf-8"))
                    except Exception:
                        out.append(buf.decode("cp1252", errors="replace"))
                    buf.clear()
                out.append(ch)
    if buf:
        try:
            out.append(buf.decode("utf-8"))
        except Exception:
            out.append(buf.decode("cp1252", errors="replace"))
    return "".join(out)

recovered = fix_mojibake(content)

def js_escape(m):
    cp = ord(m.group())
    if cp <= 0xFFFF:
        return "\\u{:04X}".format(cp)
    cp -= 0x10000
    high = 0xD800 + (cp >> 10)
    low  = 0xDC00 + (cp & 0x3FF)
    return "\\u{:04X}\\u{:04X}".format(high, low)

ascii_safe = re.sub(r"[^\x00-\x7F]", js_escape, recovered)

with open(path, "w", encoding="ascii") as f:
    f.write(ascii_safe)

sample = re.findall(r"\\u[0-9A-F]{4}", ascii_safe)
print("Done. File length: {} chars. Sample escapes: {}".format(len(ascii_safe), sample[:8]))
