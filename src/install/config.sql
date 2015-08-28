SET FOREIGN_KEY_CHECKS=0;


-- ----------------------------
-- Table structure for `dashboard_config_admin`
-- ----------------------------
DROP TABLE IF EXISTS `dashboard_config_admin`;
CREATE TABLE `dashboard_config_admin` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `link_enabled` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=latin1;

-- ----------------------------
-- Records of dashboard_config_admin
-- ----------------------------
INSERT INTO `dashboard_config_admin` VALUES ('1', '1');



-- ----------------------------
--  Table structure for `dashboard_config_email`
-- ----------------------------
DROP TABLE IF EXISTS `dashboard_config_email`;
CREATE TABLE `dashboard_config_email` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `enabled` tinyint(1) NOT NULL,
  `email_format` tinyint(1) NOT NULL,
  `from_address` varchar(50) NOT NULL,
  `text_pager` varchar(50) NOT NULL,
  `incident_greeting` varchar(1000) NOT NULL,
  `incident_update` varchar(1000) NOT NULL,
  `maintenance_greeting` varchar(1000) NOT NULL,
  `maintenance_update` varchar(1000) NOT NULL,
  `email_footer` varchar(250) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

SET FOREIGN_KEY_CHECKS = 1;

-- ----------------------------
-- Records of dashboard_config_email
-- ----------------------------
INSERT INTO `dashboard_config_email` VALUES ('1', '0', '0', '', '', 'ATTN: We are currently experiencing a service issue that is impacting one or more production services. We are actively working to resolve this issue and will update you as progress is made on a resolution. All known information about this incident is listed below.', 'ATTN: The following is an update on a service issue that is impacting one or more production services. We are actively working to resolve this issue and will update you as progress is made on a resolution. All known information about this incident is listed below.', 'ATTN: The purpose of this message is to inform you of upcoming maintenance activities within our technical infrastructure.', 'ATTN: The purpose of this message is to update you on the status of maintenance activities within our technical infrastructure.', 'This message is being sent to you from the system status dashboard.  If you would prefer not to receive future updates on system status, please notify your system administrator.');



-- ----------------------------
--  Table structure for `dashboard_config_escalation`
-- ----------------------------
DROP TABLE IF EXISTS `dashboard_config_escalation`;
CREATE TABLE `dashboard_config_escalation` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `enabled` tinyint(1) NOT NULL,
  `instructions` varchar(1000) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=latin1;

-- ----------------------------
-- Records of dashboard_config_escalation
-- ----------------------------
INSERT INTO `dashboard_config_escalation` VALUES ('1', '0', 'If you reported an incident and have not received confirmation that our engineers are investigating the problem, please use the below contacts to escalate the issue. If you are unable to reach a contact, please leave a voice message, wait 5 minutes for a response, and escalate to the next contact on the list.');



-- ----------------------------
-- Table structure for `dashboard_config_ireport`
-- ----------------------------
DROP TABLE IF EXISTS `dashboard_config_ireport`;
CREATE TABLE `dashboard_config_ireport` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `enabled` tinyint(1) NOT NULL,
  `email_enabled` tinyint(1) NOT NULL,
  `instructions` varchar(1000) NOT NULL,
  `submit_message` varchar(1000) NOT NULL,
  `upload_enabled` tinyint(1) NOT NULL,
  `upload_path` varchar(1000) NOT NULL,
  `file_size` int(11) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=latin1;

-- ----------------------------
-- Records of dashboard_config_ireport
-- ----------------------------
INSERT INTO `dashboard_config_ireport` VALUES ('1', '0', '0', 'When reporting an incident, please be as descriptive as possible about the issue you are experiencing.', 'Thank you, your incident report has been received.', '0', '', '1024');



-- ----------------------------
-- Table structure for `dashboard_config_logo`
-- ----------------------------
DROP TABLE IF EXISTS `dashboard_config_logo`;
CREATE TABLE `dashboard_config_logo` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `url` varchar(1000) NOT NULL,
  `logo_enabled` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=latin1;

-- ----------------------------
-- Records of dashboard_config_logo
-- ----------------------------
INSERT INTO `dashboard_config_logo` VALUES ('1', '', '0');



-- ----------------------------
-- Table structure for `dashboard_config_message`
-- ----------------------------
DROP TABLE IF EXISTS `dashboard_config_message`;
CREATE TABLE `dashboard_config_message` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `main` varchar(1000) NOT NULL,
  `main_enabled` tinyint(1) NOT NULL,
  `alert` varchar(1000) NOT NULL,
  `alert_enabled` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=latin1;

-- ----------------------------
-- Records of dashboard_config_message
-- ----------------------------
INSERT INTO `dashboard_config_message` VALUES ('1', 'This dashboard displays status information for all critical services. The dashboard will be updated whenever status information for any service changes.', '1', '', '0');



-- ----------------------------
-- Table structure for `dashboard_config_systemurl`
-- ----------------------------
DROP TABLE IF EXISTS `dashboard_config_systemurl`;
CREATE TABLE `dashboard_config_systemurl` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `url` varchar(250) NOT NULL,
  `url_enabled` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=latin1;

-- ----------------------------
-- Records of dashboard_config_systemurl
-- ----------------------------
INSERT INTO `dashboard_config_systemurl` VALUES ('1', '', '0');



-- ----------------------------
-- Table structure for `dashboard_status`
-- ----------------------------
DROP TABLE IF EXISTS `dashboard_status`;
CREATE TABLE `dashboard_status` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `status` varchar(10) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `status` (`status`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=latin1;

-- ----------------------------
-- Records of dashboard_status
-- ----------------------------
INSERT INTO `dashboard_status` VALUES ('1', 'planning');
INSERT INTO `dashboard_status` VALUES ('2', 'open');
INSERT INTO `dashboard_status` VALUES ('3', 'closed');
INSERT INTO `dashboard_status` VALUES ('4', 'started');
INSERT INTO `dashboard_status` VALUES ('5', 'completed');



-- ----------------------------
-- Table structure for `dashboard_type`
-- ----------------------------
DROP TABLE IF EXISTS `dashboard_type`;
CREATE TABLE `dashboard_type` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `type` varchar(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `type` (`type`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=latin1;

-- ----------------------------
-- Records of dashboard_type
-- ----------------------------
INSERT INTO `dashboard_type` VALUES ('1', 'incident');
INSERT INTO `dashboard_type` VALUES ('2', 'maintenance');