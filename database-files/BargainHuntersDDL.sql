-- ============================================================
-- BargainHunters Schema
-- ============================================================

DROP DATABASE IF EXISTS BargainHunters;

CREATE DATABASE IF NOT EXISTS BargainHunters;

USE BargainHunters;
CREATE TABLE users (
                       user_id     INT             NOT NULL AUTO_INCREMENT,
                       name        VARCHAR(100)    NOT NULL,
                       email       VARCHAR(255)    NOT NULL UNIQUE,
                       is_active   BOOLEAN         NOT NULL DEFAULT TRUE,
                       date_joined DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
                       PRIMARY KEY (user_id)
);

-- ------------------------------------------------------------

CREATE TABLE errors (
                        error_id    INT             NOT NULL AUTO_INCREMENT,
                        error_desc  TEXT            NOT NULL,
                        user_id     INT             NOT NULL,
                        PRIMARY KEY (error_id),
                        CONSTRAINT fk_errors_user
                            FOREIGN KEY (user_id) REFERENCES users(user_id)
                                ON DELETE CASCADE -- note a User will never be deleted only deactivated, in thoery this wont have to be used unless somthing big is messed up
);

-- ------------------------------------------------------------

CREATE TABLE feedback (
                          feedback_id INT             NOT NULL AUTO_INCREMENT,
                          content     TEXT            NOT NULL,
                          created_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
                          user_id     INT             NOT NULL,
                          PRIMARY KEY (feedback_id),
                          CONSTRAINT fk_feedback_user
                              FOREIGN KEY (user_id) REFERENCES users(user_id)
                                  ON DELETE CASCADE  -- note a User will never be deleted only deactivated, in thoery this wont have to be used unless somthing big is messed up

);

-- ------------------------------------------------------------

CREATE TABLE user_activity (
                               event_id        INT             NOT NULL AUTO_INCREMENT,
                               event_type      VARCHAR(100)    NOT NULL,
                               event_timestamp DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
                               user_id         INT             NOT NULL,
                               PRIMARY KEY (event_id),
                               CONSTRAINT fk_activity_user
                                   FOREIGN KEY (user_id) REFERENCES users(user_id)
                                       ON DELETE CASCADE
);



-- ------------------------------------------------------------

CREATE TABLE categories (
                            cat_id      BIGINT          NOT NULL, -- should be filled in with the coresponding ID from the ebay api
                            cat_name    VARCHAR(255)    NOT NULL,
                            url         VARCHAR(2048)   NOT NULL,
                            is_active   BOOLEAN         NOT NULL DEFAULT TRUE,
                            current_price DECIMAL(10,2) UNSIGNED ,
                            PRIMARY KEY (cat_id)
);

-- ------------------------------------------------------------

CREATE TABLE items (
                       item_id     BIGINT          NOT NULL , -- should be filled in with the coresponding ID from the ebay api
                       item_name   VARCHAR(255)    NOT NULL,
                       url         VARCHAR(2048)   NOT NULL,
                       is_active   BOOLEAN         NOT NULL DEFAULT TRUE,
                       current_price DECIMAL(10,2) UNSIGNED ,
                    PRIMARY KEY (item_id)

);

-- ------------------------------------------------------------

CREATE TABLE listings (
                          listing_id     BIGINT          NOT NULL, -- should be filled in with the coresponding ID from the ebay api
                          listing_name   VARCHAR(255)    NOT NULL,
                          url         VARCHAR(2048)   NOT NULL,
                          is_active   BOOLEAN         NOT NULL DEFAULT TRUE,
                        current_price DECIMAL(10,2) UNSIGNED ,
                              PRIMARY KEY (listing_id)

);

-- ------------------------------------------------------------
CREATE TABLE alerts (
                        alert_id        INT             NOT NULL AUTO_INCREMENT,
                        watch_type      ENUM('item', 'category', 'listing') NOT NULL,
                        date_started    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        date_ended      DATETIME,
                        is_active       BOOLEAN         NOT NULL DEFAULT TRUE,
                        drop_amt        DECIMAL(10, 2),
                        drop_percent    DECIMAL(5, 2),
                        original_price  DECIMAL(10, 2),
                        item_id         BIGINT,                    -- FK: nullable — alert targets item OR category OR listing
                        cat_id          BIGINT,                    -- FK: nullable — alert targets item OR category OR listing
                        listing_id      BIGINT,                    -- FK: nullable — alert targets item OR category OR listing
                        PRIMARY KEY (alert_id),
                        CONSTRAINT fk_alerts_item
                            FOREIGN KEY (item_id) REFERENCES items(item_id)
                                ON DELETE SET NULL,
                        CONSTRAINT fk_alerts_category
                            FOREIGN KEY (cat_id) REFERENCES categories(cat_id)
                                ON DELETE SET NULL,
                        CONSTRAINT fk_alerts_listing
                            FOREIGN KEY (listing_id) REFERENCES listings(listing_id)
                                ON DELETE SET NULL

);
-- ------------------------------------------------------------

CREATE TABLE watchlist (

                           last_checked    DATETIME,
                           user_id         INT         NOT NULL,
                           alert_id        INT         NOT NULL,
                           PRIMARY KEY (user_id,alert_id),
                           CONSTRAINT fk_watchlist_user
                               FOREIGN KEY (user_id) REFERENCES users(user_id)
                                   ON DELETE CASCADE,
                           CONSTRAINT fk_watchlist_alert
                               FOREIGN KEY (alert_id) REFERENCES alerts(alert_id)
                                   ON DELETE CASCADE

);

-- ------------------------------------------------------------

CREATE TABLE notifications (
                               notification_id INT             NOT NULL AUTO_INCREMENT,
                               content         TEXT            NOT NULL,
                               sent_date       DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
                               user_id         INT             NOT NULL,
                               alert_id        INT             NOT NULL,
                               PRIMARY KEY (notification_id),
                               CONSTRAINT fk_notif_user
                                   FOREIGN KEY (user_id) REFERENCES users(user_id)
                                       ON DELETE CASCADE,
                               CONSTRAINT fk_notif_alert
                                   FOREIGN KEY (alert_id) REFERENCES alerts(alert_id)
                                       ON DELETE CASCADE
);
-- Insert statement for users table
INSERT INTO users (name, email) VALUES
('Alice Johnson', 'alice@example.com'),
('Bob Smith', 'bob@example.com'),
('Charlie Brown', 'charlie@example.com'),
('Diana Prince', 'diana@example.com'),
('Ethan Hunt', 'ethan@example.com');
-- Insert statement for categories table
INSERT INTO categories (cat_id, cat_name, url, current_price) VALUES
(1001, 'Electronics', 'https://example.com/electronics', 250.00),
(1002, 'Fashion', 'https://example.com/fashion', 75.50),
(1003, 'Home & Garden', 'https://example.com/home', 120.99),
(1004, 'Toys', 'https://example.com/toys', 45.00),
(1005, 'Sports', 'https://example.com/sports', 89.99);
-- Insert statement for items table
INSERT INTO items (item_id, item_name, url, current_price) VALUES
(2001, 'iPhone 13', 'https://example.com/iphone13', 699.99),
(2002, 'Nike Sneakers', 'https://example.com/nike', 120.00),
(2003, 'Coffee Maker', 'https://example.com/coffee', 49.99),
(2004, 'Lego Set', 'https://example.com/lego', 59.99),
(2005, 'Basketball', 'https://example.com/basketball', 25.00);
-- Insert statement for listings table
INSERT INTO listings (listing_id, listing_name, url, current_price) VALUES
(3001, 'iPhone 13 - Used', 'https://example.com/listing1', 650.00),
(3002, 'Nike Sneakers Sale', 'https://example.com/listing2', 100.00),
(3003, 'Coffee Maker Discount', 'https://example.com/listing3', 39.99),
(3004, 'Lego Set Bundle', 'https://example.com/listing4', 55.00),
(3005, 'Basketball Deal', 'https://example.com/listing5', 20.00);
-- Insert statement for user activity table
INSERT INTO user_activity (event_type, user_id) VALUES
('login', 1),
('search_item', 2),
('add_to_watchlist', 3),
('view_listing', 1),
('logout', 4);