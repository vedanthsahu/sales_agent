import { motion } from "framer-motion";
import { Icons } from "../../constants";

export const AnimatedLogo = () => {
  return (
    <motion.div
      className="relative w-10 h-10 rounded-xl flex items-center justify-center overflow-hidden"
      animate={{
        boxShadow: [
          "0 0 0px rgba(59,130,246,0.2)",
          "0 0 18px rgba(59,130,246,0.35)",
          "0 0 0px rgba(59,130,246,0.2)"
        ]
      }}
      transition={{ duration: 3, repeat: Infinity }}
    >
      {/* Gradient Background */}
      <motion.div
        className="absolute inset-0 bg-gradient-to-tr from-primary-600 to-primary-400"
        animate={{
          rotate: [0, 360]
        }}
        transition={{
          duration: 18,
          repeat: Infinity,
          ease: "linear"
        }}
      />

      {/* Floating Icon */}
      <motion.div
        className="relative text-white"
        animate={{
          y: [-2, 2, -2],
          rotate: [-2, 2, -2]
        }}
        transition={{
          duration: 4,
          repeat: Infinity,
          ease: "easeInOut"
        }}
      >
        <Icons.Sparkles className="w-6 h-6" />
      </motion.div>

      {/* Shimmer Sweep */}
      <motion.div
        className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent"
        animate={{ x: ["-120%", "120%"] }}
        transition={{ duration: 2.5, repeat: Infinity, delay: 2 }}
      />
    </motion.div>
  );
};
