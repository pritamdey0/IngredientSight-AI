import React, { useEffect, useRef, useState } from 'react';

const VIDEO_URL =
  'https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260729_102822_0e6c87e8-c141-4744-bf32-ad30db296371.mp4';

export const ScrollVideoBackground: React.FC = () => {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [isVideoLoaded, setIsVideoLoaded] = useState(false);

  const targetProgressRef = useRef(0);
  const smoothedProgressRef = useRef(0);

  // 1. Scroll listener -> Target Progress calculation
  useEffect(() => {
    const handleScroll = () => {
      const scrollY = window.scrollY;
      const totalHeight = document.documentElement.scrollHeight - window.innerHeight;
      const progress = totalHeight > 0 ? Math.min(1, Math.max(0, scrollY / totalHeight)) : 0;
      targetProgressRef.current = progress;
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    handleScroll();
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // 2. Smooth Lerp Scroll-Scrubbing & Canvas Drawing
  useEffect(() => {
    let animId: number;

    const render = () => {
      const video = videoRef.current;
      const canvas = canvasRef.current;

      if (video && video.duration && !isNaN(video.duration) && video.duration > 0) {
        // Lerp physics: smoothed += (target - smoothed) * 0.08 for ultra smooth motion
        smoothedProgressRef.current += (targetProgressRef.current - smoothedProgressRef.current) * 0.08;
        const targetTime = smoothedProgressRef.current * Math.max(0.1, video.duration - 0.05);

        // Seek video smoothly if delta is significant and not already seeking
        if (Math.abs(video.currentTime - targetTime) > 0.05 && !video.seeking) {
          const v = video as HTMLVideoElement & { fastSeek?: (t: number) => void };
          if (typeof v.fastSeek === 'function') {
            v.fastSeek(targetTime);
          } else {
            v.currentTime = targetTime;
          }
        }

        // Draw current frame to canvas for smooth hardware-accelerated rendering
        if (canvas && video.videoWidth > 0 && video.videoHeight > 0) {
          const ctx = canvas.getContext('2d');
          if (ctx) {
            const dpr = Math.min(window.devicePixelRatio || 1, 2);
            const w = window.innerWidth;
            const h = window.innerHeight;

            if (canvas.width !== w * dpr || canvas.height !== h * dpr) {
              canvas.width = w * dpr;
              canvas.height = h * dpr;
            }

            ctx.save();
            ctx.scale(dpr, dpr);

            // Object-cover calculation
            const imgRatio = video.videoWidth / video.videoHeight;
            const screenRatio = w / h;

            let drawW, drawH, drawX, drawY;
            if (screenRatio > imgRatio) {
              drawW = w;
              drawH = w / imgRatio;
              drawX = 0;
              drawY = (h - drawH) / 2;
            } else {
              drawH = h;
              drawW = h * imgRatio;
              drawX = (w - drawW) / 2;
              drawY = 0;
            }

            ctx.clearRect(0, 0, w, h);
            ctx.drawImage(video, drawX, drawY, drawW, drawH);
            ctx.restore();
          }
        }
      }

      animId = requestAnimationFrame(render);
    };

    animId = requestAnimationFrame(render);
    return () => cancelAnimationFrame(animId);
  }, []);

  const handleLoadedData = () => {
    setIsVideoLoaded(true);
    if (videoRef.current) {
      videoRef.current.pause(); // Pause autoplay so video is driven strictly by scroll
    }
  };

  return (
    <div className="fixed inset-0 z-0 bg-[#0a0a0a] overflow-hidden pointer-events-none select-none">
      {/* 1. Cinematic Gradient & Glow Placeholder (Prevents Initial Black Flash) */}
      <div className="absolute inset-0 z-0 bg-[#0a0a0a]">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_40%,rgba(40,60,90,0.35),rgba(10,10,10,0.95))] animate-pulse" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_70%_70%,rgba(200,120,50,0.15),transparent_50%)]" />
      </div>

      {/* 2. Invisible Video Element (Used as frame source) */}
      <video
        ref={videoRef}
        src={VIDEO_URL}
        muted
        playsInline
        preload="auto"
        onCanPlay={handleLoadedData}
        onLoadedData={handleLoadedData}
        className="hidden"
      />

      {/* 3. Hardware-Accelerated Canvas Element (Smooth 60fps rendering) */}
      <canvas
        ref={canvasRef}
        className={`absolute inset-0 w-full h-full object-cover z-1 transition-opacity duration-700 ${
          isVideoLoaded ? 'opacity-100' : 'opacity-0'
        }`}
      />

      {/* 4. Ambient Vignette & Contrast Gradient Overlay */}
      <div className="absolute inset-0 z-2 bg-gradient-to-b from-black/60 via-black/20 to-black/80 pointer-events-none" />
    </div>
  );
};

export default ScrollVideoBackground;
