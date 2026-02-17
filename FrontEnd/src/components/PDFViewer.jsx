import { useEffect, useRef, useState } from 'react';
import * as pdfjsLib from 'pdfjs-dist';
import pdfWorker from 'pdfjs-dist/build/pdf.worker.mjs?url';

// Set worker source to local imported file
pdfjsLib.GlobalWorkerOptions.workerSrc = pdfWorker;

export default function PDFViewer({ file, boxes, onPageRendered }) {
    const containerRef = useRef(null);
    const [pdfDoc, setPdfDoc] = useState(null);
    const [scale, setScale] = useState(1.2);

    useEffect(() => {
        if (!file) return;

        const loadPdf = async () => {
            const arrayBuffer = await file.arrayBuffer();
            const loadingTask = pdfjsLib.getDocument(arrayBuffer);
            const doc = await loadingTask.promise;
            setPdfDoc(doc);
        };

        loadPdf();
    }, [file]);

    return (
        <div className="pdf-container" ref={containerRef}>
            {pdfDoc && Array.from({ length: pdfDoc.numPages }, (_, i) => (
                <PDFPage
                    key={i + 1}
                    pageNumber={i + 1}
                    doc={pdfDoc}
                    scale={scale}
                    boxes={boxes.filter(b => b.page === i + 1)}
                />
            ))}
        </div>
    );
}

function PDFPage({ pageNumber, doc, scale, boxes }) {
    const canvasRef = useRef(null);
    const wrapperRef = useRef(null);
    const [viewport, setViewport] = useState(null);

    useEffect(() => {
        if (!doc) return;

        doc.getPage(pageNumber).then(page => {
            const vp = page.getViewport({ scale });
            setViewport(vp);

            const canvas = canvasRef.current;
            const context = canvas.getContext('2d');
            canvas.height = vp.height;
            canvas.width = vp.width;

            const renderContext = {
                canvasContext: context,
                viewport: vp,
            };

            page.render(renderContext);
        });
    }, [doc, pageNumber, scale]);

    return (
        <div className="pdf-page-container" ref={wrapperRef} style={{ width: viewport?.width, height: viewport?.height }}>
            <canvas ref={canvasRef} />
            {viewport && boxes.map((box, idx) => {
                // box.bbox is [x0, y0, x1, y1] (pdf coords)
                // Need to transform to viewport coords
                // PDF coords: usually (0,0) is bottom-left? No, usually top-left in PDF.js?
                // pdfplumber: [x0, top, x1, bottom] (top-left origin).
                // pdf.js viewport.convertToViewportPoint supports [x, y].

                // pdfplumber: y0 is top.
                // pdf.js viewport default: (0,0) is top-left.

                // We can just scale if origin matches.
                // pdfplumber rect: [x0, y0, x1, y1]

                const [x0, y0, x1, y1] = box.bbox;
                // Simple scaling if coordinates align
                // But PDF extraction might be different units (pt vs px).
                // viewport.transform handles this.

                // Transform [x, y] using viewport.transform
                const [tx0, ty0] = viewport.convertToViewportPoint(x0, y0);
                const [tx1, ty1] = viewport.convertToViewportPoint(x1, y1);

                // Calculate width/height
                const width = tx1 - tx0;
                const height = ty1 - ty0;

                return (
                    <div
                        key={idx}
                        className="highlight-overlay"
                        style={{
                            left: tx0,
                            top: ty0,
                            width: width,
                            height: height,
                        }}
                        title={box.label}
                    />
                );
            })}
        </div>
    );
}
