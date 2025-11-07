import { useEffect, useState } from "react";
import { cn } from "@/shared/utils/cn";

interface TypingAnimationProps {
  text: string;
  duration?: number;
  className?: string;
  as?: React.ElementType;
}

export default function TypingAnimation({
  text,
  duration = 50,
  className,
  as: Component = "p",
}: TypingAnimationProps) {
  const [displayedText, setDisplayedText] = useState("");
  const [i, setI] = useState(0);

  useEffect(() => {
    setDisplayedText("");
    setI(0);
  }, [text]);

  useEffect(() => {
    const typingEffect = setInterval(() => {
      if (i < text.length) {
        setDisplayedText((prev) => prev + text.charAt(i));
        setI(i + 1);
      } else {
        clearInterval(typingEffect);
      }
    }, duration);

    return () => {
      clearInterval(typingEffect);
    };
  }, [duration, i, text]);

  return (
    <Component
      className={cn(
        "font-display text-left tracking-[-0.02em] drop-shadow-sm",
        className
      )}
    >
      {displayedText}
      {i < text.length && (
        <span className="animate-pulse">|</span>
      )}
    </Component>
  );
}
