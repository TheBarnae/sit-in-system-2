-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Mar 25, 2026 at 02:43 PM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CO NNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*update*/
--
-- Database: `sit_in_db`
--

-- --------------------------------------------------------

--
-- Table structure for table `sit_in_logs`
--

CREATE TABLE `sit_in_logs` (
  `id` int(11) NOT NULL,
  `student_id_number` varchar(20) NOT NULL,
  `purpose` varchar(100) DEFAULT NULL,
  `lab` varchar(50) DEFAULT NULL,
  `session_no` int(11) DEFAULT 1,
  `status` enum('active','completed') NOT NULL DEFAULT 'active',
  `started_at` datetime NOT NULL DEFAULT current_timestamp(),
  `ended_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `sit_in_logs`
--

INSERT INTO `sit_in_logs` (`id`, `student_id_number`, `purpose`, `lab`, `session_no`, `status`, `started_at`, `ended_at`) VALUES
(1, 'barnae', 'Java', 'LAB101', 1, 'completed', '2026-03-25 19:25:28', '2026-03-25 19:26:52'),
(2, '123456789', 'C', 'LAB102', 1, 'completed', '2026-03-25 19:32:29', '2026-03-25 19:47:24');

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `id` int(11) NOT NULL,
  `id_number` varchar(20) NOT NULL,
  `last_name` varchar(50) DEFAULT NULL,
  `first_name` varchar(50) DEFAULT NULL,
  `middle_name` varchar(50) DEFAULT NULL,
  `course` varchar(50) DEFAULT NULL,
  `course_level` varchar(20) DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `address` varchar(100) DEFAULT NULL,
  `password` varchar(255) DEFAULT NULL,
  `photo_path` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`id`, `id_number`, `last_name`, `first_name`, `middle_name`, `course`, `course_level`, `email`, `address`, `password`, `photo_path`) VALUES
(1, '23743842', 'Garcia', 'Nichole', 'Maraguinot', 'BSIT', '3', 'garcia@email.com', '57 Sampaguita St, PBN Housing, Cebu City', 'scrypt:32768:8:1$L43En3n6cnHkTzSz$f2bc7f3b73fad19850d382af1885ad259a843c86108bd5d5d59646032a32182a530d811eba8c1296872636dc476cb2fcaaa2bd31744d734317b9e3d924f31e55', 'uploads/23743842.png'),
(2, '123456789', 'Garcia', 'Sean', 'Maraguinot', 'BSIT', '1', '123@gmail.com', '57 Sampaguita St, PBN Housing', 'scrypt:32768:8:1$9AgmQ7iYe9v9DlAD$f019d5f780dc5a9b699e93329908245f5e863bd8edae5653af1d9a6e126b2e308bb8315781037cd6450b809bd1dbbb0c71d030394dbf3db009e96fc00c24951a', 'uploads/123456789.jpg'),
(3, 'adm-1234', 'Admin', 'CCS', '', 'ADMIN', '0', 'admin@example.com', 'N/A', 'scrypt:32768:8:1$awa3xo6nSwqGIpLJ$6cdf5a11b7b7d237eadc4fac988ba6308558e4604e5ac202ba76f03c9b748d18c4ffab6e45232a9a536589d55a90c4dc913355da1832d26bc7ff5553a06d9ffb', NULL),
(5, 'barnae', 'Garcia', 'Nichole Anne', 'Maraguinot', 'BSIT', '3', 'xyeahgirlx@gmail.com', '8V8W+MX7', 'scrypt:32768:8:1$iJeh4HsPfXDbfgNm$ca405eb00ef858c3d1d16a3a7b4a71aa9fa5955c9c146d1ed186cf223a20df900560d602ac97c75506495482ac2c497e88adb7c63facf1b39de558381ae3c9d9', NULL);

-- --------------------------------------------------------

--
-- Table structure for table `user_feedback`
--

CREATE TABLE `user_feedback` (
  `id` int(11) NOT NULL,
  `student_id_number` varchar(20) NOT NULL,
  `sit_in_log_id` int(11) DEFAULT NULL,
  `rating` tinyint(4) DEFAULT NULL,
  `feedback_text` text NOT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `user_feedback`
--

INSERT INTO `user_feedback` (`id`, `student_id_number`, `sit_in_log_id`, `rating`, `feedback_text`, `created_at`) VALUES
(1, '123456789', 2, 5, 'The experience was great!', '2026-03-25 20:47:02');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `sit_in_logs`
--
ALTER TABLE `sit_in_logs`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_student_id_number` (`student_id_number`),
  ADD KEY `idx_status` (`status`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uq_users_id_number` (`id_number`);

--
-- Indexes for table `user_feedback`
--
ALTER TABLE `user_feedback`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_student_id_number` (`student_id_number`),
  ADD KEY `idx_sit_in_log_id` (`sit_in_log_id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `sit_in_logs`
--
ALTER TABLE `sit_in_logs`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT for table `user_feedback`
--
ALTER TABLE `user_feedback`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `user_feedback`
--
ALTER TABLE `user_feedback`
  ADD CONSTRAINT `fk_user_feedback_sit_in` FOREIGN KEY (`sit_in_log_id`) REFERENCES `sit_in_logs` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `fk_user_feedback_student` FOREIGN KEY (`student_id_number`) REFERENCES `users` (`id_number`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
