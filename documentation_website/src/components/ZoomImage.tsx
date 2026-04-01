import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Maximize2, X } from 'lucide-react';
import clsx from 'clsx';
import ReactDOM from 'react-dom';
import useBaseUrl from '@docusaurus/useBaseUrl';

interface ZoomImageProps {
  src: string;
  alt: string;
  caption?: string;
}

const ZoomImage: React.FC<ZoomImageProps> = ({ src, alt, caption }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [isHovered, setIsHovered] = useState(false);
  const fullSrc = useBaseUrl(src);

  // Handle escape key
  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setIsOpen(false);
    };
    if (isOpen) {
      window.addEventListener('keydown', handleEsc);
      document.body.style.overflow = 'hidden';
    }
    return () => {
      window.removeEventListener('keydown', handleEsc);
      document.body.style.overflow = 'auto';
    };
  }, [isOpen]);

  const toggleOpen = () => setIsOpen(!isOpen);

  // Use portal for the overlay to ensure it's on top of everything
  const overlay = (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.3 }}
          className="zoom-image-overlay"
          onClick={toggleOpen}
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            width: '100vw',
            height: '100vh',
            zIndex: 9999,
            backgroundColor: 'rgba(0, 0, 0, 0.4)',
            backdropFilter: 'blur(12px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'zoom-out',
          }}
        >
          {/* Close button */}
          <motion.button
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            className="zoom-image-close"
            onClick={(e) => {
              e.stopPropagation();
              setIsOpen(false);
            }}
            style={{
              position: 'fixed',
              top: '20px',
              right: '20px',
              background: 'rgba(255, 255, 255, 0.1)',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              borderRadius: '50%',
              width: '40px',
              height: '40px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'white',
              cursor: 'pointer',
              zIndex: 10000,
            }}
          >
            <X size={20} />
          </motion.button>

          {/* Enlarged Image */}
          <motion.div
            layoutId={`image-${src}`}
            transition={{
              type: 'spring',
              stiffness: 260,
              damping: 30
            }}
            className="zoom-image-container"
            onClick={(e) => e.stopPropagation()}
            style={{
              position: 'relative',
              maxWidth: '75%',
              maxHeight: '75%',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              paddingBottom: '10vh',
            }}
          >
            <img
              src={fullSrc}
              alt={alt}
              style={{
                width: '100%',
                height: 'auto',
                borderRadius: '12px',
                boxShadow: '0 20px 40px rgba(0,0,0,0.4)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
              }}
            />
            {caption && (
              <motion.p
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                style={{
                  color: 'white',
                  marginTop: '1.5rem',
                  fontSize: '1rem',
                  fontWeight: 500,
                  textAlign: 'center',
                  background: 'rgba(0,0,0,0.4)',
                  padding: '8px 16px',
                  borderRadius: '20px',
                  backdropFilter: 'blur(4px)',
                }}
              >
                {caption}
              </motion.p>
            )}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );

  return (
    <>
      <div
        className="zoom-image-thumbnail-container"
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        onClick={toggleOpen}
        style={{
          position: 'relative',
          cursor: 'zoom-in',
          borderRadius: '8px',
          overflow: 'hidden',
          width: '100%',
        }}
      >
        <motion.div
          layoutId={`image-${src}`}
          style={{ width: '100%', height: '100%' }}
        >
          <img
            src={fullSrc}
            alt={alt}
            style={{
              width: '100%',
              display: 'block',
            }}
          />
        </motion.div>

        {/* Minimal Corner Expand Icon */}
        <AnimatePresence>
          {isHovered && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              style={{
                position: 'absolute',
                bottom: '8px',
                right: '8px',
                pointerEvents: 'none',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                background: 'rgba(255, 255, 255, 0.95)',
                borderRadius: '4px',
                width: '24px',
                height: '24px',
                boxShadow: '0 2px 6px rgba(0,0,0,0.15)',
                color: '#1a1d22',
              }}
            >
              <Maximize2 size={14} strokeWidth={2.5} style={{ flexShrink: 0 }} />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {typeof document !== 'undefined' && ReactDOM.createPortal(overlay, document.body)}
    </>
  );
};

export default ZoomImage;
