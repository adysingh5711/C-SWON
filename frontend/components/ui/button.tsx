import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 active:scale-[0.98] hover:-translate-y-0.5 hover:shadow-md",
  {
    variants: {
      variant: {
        default: "bg-[var(--color-teal)] text-white hover:bg-[var(--color-teal-dim)] shadow-sm",
        destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        outline: "border border-[var(--color-border-emphasis)] bg-transparent hover:bg-[var(--color-surface-1)] text-[var(--color-ink)]",
        secondary: "bg-[var(--color-surface-2)] text-[var(--color-ink)] hover:bg-[var(--color-surface-3)]",
        ghost: "hover:bg-[var(--color-surface-1)] hover:text-[var(--color-ink)] hover:shadow-none hover:-translate-y-0 active:scale-100",
        link: "text-[var(--color-teal)] underline-offset-4 hover:underline hover:shadow-none hover:-translate-y-0 active:scale-100",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3",
        lg: "h-11 rounded-md px-8",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
