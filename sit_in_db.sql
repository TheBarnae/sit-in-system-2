-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Mar 23, 2026 at 02:40 PM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

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

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `id` int(11) NOT NULL,
  `id_number` varchar(20) DEFAULT NULL,
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
(1, '23743842', 'Garcia', 'Nichole', 'Maraguinot', 'BSIT', '3', 'garcia@email.com', '57 Sampaguita St, PBN Housing, Cebu City', 'scrypt:32768:8:1$4bZQlvXzoYY5FDki$52cfcdfb33eda4cbf268391590b171c45438e8b1bfc1f5486199d72f3085c2afb33ba6caaeebad321327a07a510a3ff8dd52bc59c3893b7852e3a34ed011445f', NULL),
(2, '123456789', 'Garcia', 'Sean', 'Maraguinot', 'BSIT', '1', '123@gmail.com', '57 Sampaguita St, PBN Housing', 'scrypt:32768:8:1$9AgmQ7iYe9v9DlAD$f019d5f780dc5a9b699e93329908245f5e863bd8edae5653af1d9a6e126b2e308bb8315781037cd6450b809bd1dbbb0c71d030394dbf3db009e96fc00c24951a', 'uploads/123456789.jpg'),
(3, 'adm-1234', 'Admin', 'CCS', '', 'ADMIN', '0', 'admin@example.com', 'N/A', 'scrypt:32768:8:1$awa3xo6nSwqGIpLJ$6cdf5a11b7b7d237eadc4fac988ba6308558e4604e5ac202ba76f03c9b748d18c4ffab6e45232a9a536589d55a90c4dc913355da1832d26bc7ff5553a06d9ffb', NULL);

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
  ADD PRIMARY KEY (`id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT for table `sit_in_logs`
--
ALTER TABLE `sit_in_logs`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
