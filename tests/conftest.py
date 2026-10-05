import pytest


@pytest.fixture
def planning_pdf(tmp_path):
    """A valid one-page planning PDF; no parser or provider mocks."""
    text = b"BT /F1 18 Tf 72 720 Td (Solar development - capacity 12 MW) Tj ET"
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length "
        + str(len(text)).encode()
        + b" >>\nstream\n"
        + text
        + b"\nendstream",
    ]
    content = b"%PDF-1.4\n"
    offsets = [0]
    for number, obj in enumerate(objects, 1):
        offsets.append(len(content))
        content += str(number).encode() + b" 0 obj\n" + obj + b"\nendobj\n"
    xref = len(content)
    content += b"xref\n0 6\n0000000000 65535 f \n"
    for offset in offsets[1:]:
        content += f"{offset:010} 00000 n \n".encode()
    content += (
        b"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n"
        + str(xref).encode()
        + b"\n%%EOF\n"
    )
    path = tmp_path / "planning.pdf"
    path.write_bytes(content)
    return path
