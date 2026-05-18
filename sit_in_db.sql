-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: May 04, 2026 at 03:59 PM
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
-- Table structure for table `announcements`
--

CREATE TABLE `announcements` (
  `id` int(11) NOT NULL,
  `author` varchar(100) NOT NULL,
  `body` text NOT NULL,
  `created_by_id` varchar(20) DEFAULT NULL,
  `status` enum('active','archived') NOT NULL DEFAULT 'active',
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `pinned` tinyint(1) NOT NULL DEFAULT 0,
  `target_course` varchar(50) DEFAULT NULL,
  `target_level` varchar(20) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `announcements`
--

INSERT INTO `announcements` (`id`, `author`, `body`, `created_by_id`, `status`, `created_at`, `pinned`, `target_course`, `target_level`) VALUES
(1, 'CCS Admin', 'Test', 'adm-1234', 'archived', '2026-04-14 01:22:42', 0, NULL, NULL),
(2, 'CCS Admin', 'WELCOME STUDENTS!', 'adm-1234', 'active', '2026-04-14 02:16:30', 1, NULL, NULL),
(3, 'CCS Admin', 'THIS IS AN ANNOUNCEMENT!', 'adm-1234', 'active', '2026-04-22 21:33:25', 0, NULL, NULL),
(4, 'CCS Admin', 'New announcement!', 'adm-1234', 'active', '2026-04-22 22:07:10', 0, NULL, NULL);

-- --------------------------------------------------------

--
-- Table structure for table `reservations`
--

CREATE TABLE `reservations` (
  `id` int(11) NOT NULL,
  `student_id_number` varchar(20) NOT NULL,
  `lab_code` varchar(20) NOT NULL,
  `seat_no` int(11) NOT NULL,
  `purpose` varchar(100) DEFAULT NULL,
  `reservation_date` date NOT NULL,
  `reservation_slot` varchar(20) NOT NULL,
  `status` enum('pending','approved','checked_in','denied','cancelled','no_show') NOT NULL DEFAULT 'pending',
  `admin_note` varchar(255) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `decided_at` datetime DEFAULT NULL,
  `decided_by` varchar(20) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `reservations`
--

INSERT INTO `reservations` (`id`, `student_id_number`, `lab_code`, `seat_no`, `purpose`, `reservation_date`, `reservation_slot`, `status`, `admin_note`, `created_at`, `decided_at`, `decided_by`) VALUES
(1, 'admin-seat-block', 'LAB524', 4, 'Admin seat block', '2026-04-13', '07:30-09:00', 'approved', 'Occupied by admin seat panel', '2026-04-13 22:32:37', '2026-04-13 22:32:37', 'adm-1234'),
(2, 'admin-seat-block', 'LAB524', 3, 'Admin seat block', '2026-04-13', '07:30-09:00', 'approved', 'Occupied by admin seat panel', '2026-04-13 22:32:40', '2026-04-13 22:32:40', 'adm-1234'),
(3, 'admin-seat-block', 'LAB524', 5, 'Admin seat block', '2026-04-13', '07:30-09:00', 'cancelled', 'Released from admin seat panel', '2026-04-13 22:32:43', '2026-04-13 22:32:44', 'adm-1234'),
(4, 'admin-seat-block', 'LAB524', 5, 'Admin seat block', '2026-04-13', '07:30-09:00', 'approved', 'Occupied by admin seat panel', '2026-04-13 22:32:45', '2026-04-13 22:32:45', 'adm-1234'),
(5, 'admin-seat-block', 'LAB524', 10, 'Admin seat block', '2026-04-13', '07:30-09:00', 'approved', 'Occupied by admin seat panel', '2026-04-13 22:32:45', '2026-04-13 22:32:45', 'adm-1234'),
(6, 'admin-seat-block', 'LAB524', 9, 'Admin seat block', '2026-04-13', '07:30-09:00', 'approved', 'Occupied by admin seat panel', '2026-04-13 22:32:45', '2026-04-13 22:32:45', 'adm-1234'),
(7, 'admin-seat-block', 'LAB524', 8, 'Admin seat block', '2026-04-13', '07:30-09:00', 'approved', 'Occupied by admin seat panel', '2026-04-13 22:32:46', '2026-04-13 22:32:46', 'adm-1234'),
(8, 'barnae', 'LAB524', 1, 'Java', '2026-04-13', '07:30-09:00', 'denied', NULL, '2026-04-13 23:04:00', '2026-04-13 23:05:25', 'adm-1234'),
(9, '23743842', 'LAB524', 2, 'C', '2026-04-13', '07:30-09:00', 'checked_in', NULL, '2026-04-13 23:05:03', '2026-04-14 02:17:17', 'adm-1234'),
(10, 'barnae', 'LAB524', 1, 'C', '2026-04-14', '07:30-09:00', 'denied', 'double', '2026-04-14 02:16:08', '2026-04-14 02:17:13', 'adm-1234'),
(11, '62746040', 'LAB524', 2, 'Java', '2026-04-22', '07:30-09:00', 'checked_in', NULL, '2026-04-22 21:32:15', '2026-04-22 21:32:42', 'adm-1234'),
(12, 'admin-seat-block', 'LAB524', 3, 'Admin seat block', '2026-04-22', '07:30-09:00', 'approved', 'Occupied by admin seat panel', '2026-04-22 21:32:46', '2026-04-22 21:32:46', 'adm-1234'),
(13, 'admin-seat-block', 'LAB524', 4, 'Admin seat block', '2026-04-22', '07:30-09:00', 'approved', 'Occupied by admin seat panel', '2026-04-22 21:32:47', '2026-04-22 21:32:47', 'adm-1234'),
(14, '62746040', 'LAB528', 2, 'JavaScript', '2026-04-22', '07:30-09:00', 'checked_in', NULL, '2026-04-22 22:07:42', '2026-04-22 22:07:55', 'adm-1234'),
(15, 'admin-seat-block', 'LAB524', 1, 'Admin seat block', '2026-05-04', '07:30-09:00', 'cancelled', 'Released from admin seat panel', '2026-05-04 21:54:41', '2026-05-04 21:54:48', 'adm-1234'),
(16, 'admin-seat-block', 'LAB524', 2, 'Admin seat block', '2026-05-04', '07:30-09:00', 'cancelled', 'Released from admin seat panel', '2026-05-04 21:54:41', '2026-05-04 21:54:48', 'adm-1234'),
(17, 'admin-seat-block', 'LAB524', 3, 'Admin seat block', '2026-05-04', '07:30-09:00', 'cancelled', 'Released from admin seat panel', '2026-05-04 21:54:41', '2026-05-04 21:54:48', 'adm-1234'),
(18, 'admin-seat-block', 'LAB524', 4, 'Admin seat block', '2026-05-04', '07:30-09:00', 'cancelled', 'Released from admin seat panel', '2026-05-04 21:54:41', '2026-05-04 21:54:48', 'adm-1234'),
(19, 'admin-seat-block', 'LAB524', 5, 'Admin seat block', '2026-05-04', '07:30-09:00', 'cancelled', 'Released from admin seat panel', '2026-05-04 21:54:41', '2026-05-04 21:54:48', 'adm-1234'),
(20, 'admin-seat-block', 'LAB524', 6, 'Admin seat block', '2026-05-04', '07:30-09:00', 'cancelled', 'Released from admin seat panel', '2026-05-04 21:54:41', '2026-05-04 21:54:48', 'adm-1234'),
(21, 'admin-seat-block', 'LAB524', 7, 'Admin seat block', '2026-05-04', '07:30-09:00', 'cancelled', 'Released from admin seat panel', '2026-05-04 21:54:41', '2026-05-04 21:54:48', 'adm-1234'),
(22, 'admin-seat-block', 'LAB524', 8, 'Admin seat block', '2026-05-04', '07:30-09:00', 'cancelled', 'Released from admin seat panel', '2026-05-04 21:54:41', '2026-05-04 21:54:48', 'adm-1234'),
(23, 'admin-seat-block', 'LAB524', 9, 'Admin seat block', '2026-05-04', '07:30-09:00', 'cancelled', 'Released from admin seat panel', '2026-05-04 21:54:41', '2026-05-04 21:54:48', 'adm-1234'),
(24, 'admin-seat-block', 'LAB524', 10, 'Admin seat block', '2026-05-04', '07:30-09:00', 'cancelled', 'Released from admin seat panel', '2026-05-04 21:54:41', '2026-05-04 21:54:48', 'adm-1234'),
(25, 'admin-seat-block', 'LAB524', 11, 'Admin seat block', '2026-05-04', '07:30-09:00', 'cancelled', 'Released from admin seat panel', '2026-05-04 21:54:41', '2026-05-04 21:54:48', 'adm-1234'),
(26, 'admin-seat-block', 'LAB524', 12, 'Admin seat block', '2026-05-04', '07:30-09:00', 'cancelled', 'Released from admin seat panel', '2026-05-04 21:54:41', '2026-05-04 21:54:48', 'adm-1234'),
(27, 'admin-seat-block', 'LAB524', 13, 'Admin seat block', '2026-05-04', '07:30-09:00', 'cancelled', 'Released from admin seat panel', '2026-05-04 21:54:41', '2026-05-04 21:54:48', 'adm-1234'),
(28, 'admin-seat-block', 'LAB524', 14, 'Admin seat block', '2026-05-04', '07:30-09:00', 'cancelled', 'Released from admin seat panel', '2026-05-04 21:54:41', '2026-05-04 21:54:48', 'adm-1234'),
(29, 'admin-seat-block', 'LAB524', 15, 'Admin seat block', '2026-05-04', '07:30-09:00', 'cancelled', 'Released from admin seat panel', '2026-05-04 21:54:41', '2026-05-04 21:54:48', 'adm-1234'),
(30, 'admin-seat-block', 'LAB524', 16, 'Admin seat block', '2026-05-04', '07:30-09:00', 'cancelled', 'Released from admin seat panel', '2026-05-04 21:54:41', '2026-05-04 21:54:48', 'adm-1234'),
(31, 'admin-seat-block', 'LAB524', 17, 'Admin seat block', '2026-05-04', '07:30-09:00', 'cancelled', 'Released from admin seat panel', '2026-05-04 21:54:41', '2026-05-04 21:54:48', 'adm-1234'),
(32, 'admin-seat-block', 'LAB524', 18, 'Admin seat block', '2026-05-04', '07:30-09:00', 'cancelled', 'Released from admin seat panel', '2026-05-04 21:54:41', '2026-05-04 21:54:48', 'adm-1234'),
(33, 'admin-seat-block', 'LAB524', 19, 'Admin seat block', '2026-05-04', '07:30-09:00', 'cancelled', 'Released from admin seat panel', '2026-05-04 21:54:41', '2026-05-04 21:54:48', 'adm-1234'),
(34, 'admin-seat-block', 'LAB524', 20, 'Admin seat block', '2026-05-04', '07:30-09:00', 'cancelled', 'Released from admin seat panel', '2026-05-04 21:54:41', '2026-05-04 21:54:48', 'adm-1234'),
(35, 'admin-seat-block', 'LAB524', 21, 'Admin seat block', '2026-05-04', '07:30-09:00', 'cancelled', 'Released from admin seat panel', '2026-05-04 21:54:41', '2026-05-04 21:54:48', 'adm-1234'),
(36, 'admin-seat-block', 'LAB524', 22, 'Admin seat block', '2026-05-04', '07:30-09:00', 'cancelled', 'Released from admin seat panel', '2026-05-04 21:54:41', '2026-05-04 21:54:48', 'adm-1234'),
(37, 'admin-seat-block', 'LAB524', 23, 'Admin seat block', '2026-05-04', '07:30-09:00', 'cancelled', 'Released from admin seat panel', '2026-05-04 21:54:41', '2026-05-04 21:54:48', 'adm-1234'),
(38, 'admin-seat-block', 'LAB524', 24, 'Admin seat block', '2026-05-04', '07:30-09:00', 'cancelled', 'Released from admin seat panel', '2026-05-04 21:54:41', '2026-05-04 21:54:48', 'adm-1234'),
(39, 'admin-seat-block', 'LAB524', 25, 'Admin seat block', '2026-05-04', '07:30-09:00', 'cancelled', 'Released from admin seat panel', '2026-05-04 21:54:41', '2026-05-04 21:54:48', 'adm-1234'),
(40, 'admin-seat-block', 'LAB524', 26, 'Admin seat block', '2026-05-04', '07:30-09:00', 'cancelled', 'Released from admin seat panel', '2026-05-04 21:54:41', '2026-05-04 21:54:48', 'adm-1234'),
(41, 'admin-seat-block', 'LAB524', 27, 'Admin seat block', '2026-05-04', '07:30-09:00', 'cancelled', 'Released from admin seat panel', '2026-05-04 21:54:41', '2026-05-04 21:54:48', 'adm-1234'),
(42, 'admin-seat-block', 'LAB524', 28, 'Admin seat block', '2026-05-04', '07:30-09:00', 'cancelled', 'Released from admin seat panel', '2026-05-04 21:54:41', '2026-05-04 21:54:48', 'adm-1234'),
(43, 'admin-seat-block', 'LAB524', 29, 'Admin seat block', '2026-05-04', '07:30-09:00', 'cancelled', 'Released from admin seat panel', '2026-05-04 21:54:41', '2026-05-04 21:54:48', 'adm-1234'),
(44, 'admin-seat-block', 'LAB524', 30, 'Admin seat block', '2026-05-04', '07:30-09:00', 'cancelled', 'Released from admin seat panel', '2026-05-04 21:54:41', '2026-05-04 21:54:48', 'adm-1234'),
(45, 'admin-seat-block', 'LAB524', 31, 'Admin seat block', '2026-05-04', '07:30-09:00', 'cancelled', 'Released from admin seat panel', '2026-05-04 21:54:41', '2026-05-04 21:54:48', 'adm-1234'),
(46, 'admin-seat-block', 'LAB524', 32, 'Admin seat block', '2026-05-04', '07:30-09:00', 'cancelled', 'Released from admin seat panel', '2026-05-04 21:54:41', '2026-05-04 21:54:48', 'adm-1234'),
(47, 'admin-seat-block', 'LAB524', 33, 'Admin seat block', '2026-05-04', '07:30-09:00', 'cancelled', 'Released from admin seat panel', '2026-05-04 21:54:41', '2026-05-04 21:54:48', 'adm-1234'),
(48, 'admin-seat-block', 'LAB524', 34, 'Admin seat block', '2026-05-04', '07:30-09:00', 'cancelled', 'Released from admin seat panel', '2026-05-04 21:54:41', '2026-05-04 21:54:48', 'adm-1234'),
(49, 'admin-seat-block', 'LAB524', 35, 'Admin seat block', '2026-05-04', '07:30-09:00', 'cancelled', 'Released from admin seat panel', '2026-05-04 21:54:41', '2026-05-04 21:54:48', 'adm-1234'),
(50, 'admin-seat-block', 'LAB524', 36, 'Admin seat block', '2026-05-04', '07:30-09:00', 'cancelled', 'Released from admin seat panel', '2026-05-04 21:54:41', '2026-05-04 21:54:48', 'adm-1234'),
(51, 'admin-seat-block', 'LAB524', 37, 'Admin seat block', '2026-05-04', '07:30-09:00', 'cancelled', 'Released from admin seat panel', '2026-05-04 21:54:41', '2026-05-04 21:54:48', 'adm-1234'),
(52, 'admin-seat-block', 'LAB524', 38, 'Admin seat block', '2026-05-04', '07:30-09:00', 'cancelled', 'Released from admin seat panel', '2026-05-04 21:54:41', '2026-05-04 21:54:48', 'adm-1234'),
(53, 'admin-seat-block', 'LAB524', 39, 'Admin seat block', '2026-05-04', '07:30-09:00', 'cancelled', 'Released from admin seat panel', '2026-05-04 21:54:41', '2026-05-04 21:54:48', 'adm-1234'),
(54, 'admin-seat-block', 'LAB524', 40, 'Admin seat block', '2026-05-04', '07:30-09:00', 'cancelled', 'Released from admin seat panel', '2026-05-04 21:54:41', '2026-05-04 21:54:48', 'adm-1234'),
(55, 'admin-seat-block', 'LAB524', 41, 'Admin seat block', '2026-05-04', '07:30-09:00', 'cancelled', 'Released from admin seat panel', '2026-05-04 21:54:41', '2026-05-04 21:54:48', 'adm-1234'),
(56, 'admin-seat-block', 'LAB524', 42, 'Admin seat block', '2026-05-04', '07:30-09:00', 'cancelled', 'Released from admin seat panel', '2026-05-04 21:54:41', '2026-05-04 21:54:48', 'adm-1234'),
(57, 'admin-seat-block', 'LAB524', 43, 'Admin seat block', '2026-05-04', '07:30-09:00', 'cancelled', 'Released from admin seat panel', '2026-05-04 21:54:41', '2026-05-04 21:54:48', 'adm-1234'),
(58, 'admin-seat-block', 'LAB524', 44, 'Admin seat block', '2026-05-04', '07:30-09:00', 'cancelled', 'Released from admin seat panel', '2026-05-04 21:54:41', '2026-05-04 21:54:48', 'adm-1234'),
(59, 'admin-seat-block', 'LAB524', 45, 'Admin seat block', '2026-05-04', '07:30-09:00', 'cancelled', 'Released from admin seat panel', '2026-05-04 21:54:41', '2026-05-04 21:54:48', 'adm-1234'),
(60, 'admin-seat-block', 'LAB524', 46, 'Admin seat block', '2026-05-04', '07:30-09:00', 'cancelled', 'Released from admin seat panel', '2026-05-04 21:54:41', '2026-05-04 21:54:48', 'adm-1234'),
(61, 'admin-seat-block', 'LAB524', 47, 'Admin seat block', '2026-05-04', '07:30-09:00', 'cancelled', 'Released from admin seat panel', '2026-05-04 21:54:41', '2026-05-04 21:54:48', 'adm-1234'),
(62, 'admin-seat-block', 'LAB524', 48, 'Admin seat block', '2026-05-04', '07:30-09:00', 'cancelled', 'Released from admin seat panel', '2026-05-04 21:54:41', '2026-05-04 21:54:48', 'adm-1234'),
(63, 'admin-seat-block', 'LAB524', 49, 'Admin seat block', '2026-05-04', '07:30-09:00', 'cancelled', 'Released from admin seat panel', '2026-05-04 21:54:41', '2026-05-04 21:54:48', 'adm-1234'),
(64, 'admin-seat-block', 'LAB524', 50, 'Admin seat block', '2026-05-04', '07:30-09:00', 'cancelled', 'Released from admin seat panel', '2026-05-04 21:54:41', '2026-05-04 21:54:48', 'adm-1234'),
(65, 'admin-seat-block', 'LAB524', 5, 'Admin seat block', '2026-05-04', '07:30-09:00', 'cancelled', 'Released from admin seat panel', '2026-05-04 21:54:53', '2026-05-04 21:54:55', 'adm-1234');

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
(2, '123456789', 'C', 'LAB102', 1, 'completed', '2026-03-25 19:32:29', '2026-03-25 19:47:24'),
(3, '23743842', 'General use', 'LAB524', 1, 'completed', '2026-04-14 02:17:17', '2026-04-14 02:17:26'),
(4, '62746040', 'General use', 'LAB524', 1, 'completed', '2026-04-22 21:32:42', '2026-04-22 21:32:58'),
(5, '62746040', 'General use', 'LAB528', 2, 'completed', '2026-04-22 22:07:55', '2026-04-22 22:08:05');

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
  `lab_assigned` varchar(20) DEFAULT NULL,
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
(5, 'barnae', 'Garcia', 'Nichole Anne', 'Maraguinot', 'BSIT', '3', 'xyeahgirlx@gmail.com', '8V8W+MX7', 'scrypt:32768:8:1$iJeh4HsPfXDbfgNm$ca405eb00ef858c3d1d16a3a7b4a71aa9fa5955c9c146d1ed186cf223a20df900560d602ac97c75506495482ac2c497e88adb7c63facf1b39de558381ae3c9d9', NULL),
(6, '62746040', 'Garcia', 'Nichole', 'Maraguinot', 'BSIT', '3', 'email@email.com', '1234 St. ', 'scrypt:32768:8:1$z2jxVP8xvA9EKS5i$ba0df74957a5f748fce82f8d7db5d5be2cd36e33a38f445326ff4a1df22e369bf45b3de1eeaf111002859402391edc38eff4a793755c445bd0bf7ab3c4704def', 'uploads/62746040.png');

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
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `admin_feedback_text` text DEFAULT NULL,
  `admin_points_reason` text DEFAULT NULL,
  `points_awarded` int(11) NOT NULL DEFAULT 0,
  `tidiness_status` enum('tidy','not_tidy') DEFAULT NULL,
  `admin_reviewed_at` datetime DEFAULT NULL,
  `admin_reviewer_id` varchar(20) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `user_feedback`
--

INSERT INTO `user_feedback` (`id`, `student_id_number`, `sit_in_log_id`, `rating`, `feedback_text`, `created_at`, `admin_feedback_text`, `admin_points_reason`, `points_awarded`, `tidiness_status`, `admin_reviewed_at`, `admin_reviewer_id`) VALUES
(1, '123456789', 2, 5, 'The experience was great!', '2026-03-25 20:47:02', 'Left the pc with tidiness!', 'Cleanliness', 2, 'tidy', '2026-04-22 21:34:40', 'adm-1234'),
(2, '62746040', 4, 4, 'The experience was great!', '2026-04-22 22:05:50', 'Good', 'Cleanliness', 5, 'tidy', '2026-04-22 22:06:56', 'adm-1234'),
(3, '62746040', 5, 4, 'The admins were nice', '2026-04-22 22:08:22', 'adadwasd', 'Good student', 2, NULL, '2026-04-22 22:08:55', 'adm-1234');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `announcements`
--
ALTER TABLE `announcements`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_announcements_status` (`status`),
  ADD KEY `idx_announcements_created_at` (`created_at`);

--
-- Indexes for table `reservations`
--
ALTER TABLE `reservations`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_reservation_student` (`student_id_number`),
  ADD KEY `idx_reservation_lab_date_slot` (`lab_code`,`reservation_date`,`reservation_slot`),
  ADD KEY `idx_reservation_status` (`status`);

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
-- AUTO_INCREMENT for table `announcements`
--
ALTER TABLE `announcements`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT for table `reservations`
--
ALTER TABLE `reservations`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=66;

--
-- AUTO_INCREMENT for table `sit_in_logs`
--
ALTER TABLE `sit_in_logs`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- AUTO_INCREMENT for table `user_feedback`
--
ALTER TABLE `user_feedback`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

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
