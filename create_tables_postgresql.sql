-- AI旅行规划师数据库表创建脚本 (PostgreSQL)
-- 创建数据库: ai_travel_planner
-- 连接字符串: postgresql://username:password@localhost:5432/ai_travel_planner

-- 创建用户表
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    preferences JSONB DEFAULT '{}'::jsonb
);

-- 创建用户表索引
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_phone_number ON users(phone_number);

-- 创建行程表
CREATE TABLE trips (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    title VARCHAR(200) NOT NULL,
    destination VARCHAR(100) NOT NULL,
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,
    total_budget DECIMAL(10,2) DEFAULT 0.00,
    actual_expense DECIMAL(10,2) DEFAULT 0.00,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 创建行程表索引
CREATE INDEX idx_trips_user_id ON trips(user_id);
CREATE INDEX idx_trips_start_date ON trips(start_date);

-- 创建行程详情表
CREATE TABLE trip_details (
    id SERIAL PRIMARY KEY,
    trip_id INTEGER NOT NULL,
    day INTEGER NOT NULL,
    type VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    location JSONB,
    address VARCHAR(500),
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    description TEXT,
    price DECIMAL(10,2) DEFAULT 0.00,
    notes TEXT,
    images JSONB,
    FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE CASCADE
);

-- 创建行程详情表索引
CREATE INDEX idx_trip_details_trip_id ON trip_details(trip_id);
CREATE INDEX idx_trip_details_day ON trip_details(day);
CREATE INDEX idx_trip_details_type ON trip_details(type);

-- 创建费用记录表
CREATE TABLE expenses (
    id SERIAL PRIMARY KEY,
    trip_id INTEGER NOT NULL,
    category VARCHAR(50) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'CNY',
    date TIMESTAMP NOT NULL,
    description VARCHAR(500),
    receipt_image VARCHAR(500),
    FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE CASCADE
);

-- 创建费用记录表索引
CREATE INDEX idx_expenses_trip_id ON expenses(trip_id);
CREATE INDEX idx_expenses_category ON expenses(category);
CREATE INDEX idx_expenses_date ON expenses(date);

-- 插入示例数据（可选）
INSERT INTO users (username, phone_number, password_hash, preferences) VALUES 
('testuser', '13800138000', '$2b$12$examplehash', '{"theme": "light", "language": "zh-CN"}');

INSERT INTO trips (user_id, title, destination, start_date, end_date, total_budget) VALUES 
(1, '北京三日游', '北京', '2024-01-15 00:00:00', '2024-01-18 00:00:00', 5000.00);

-- 显示表结构信息
\dt

-- 显示表详细信息
\d+ users
\d+ trips
\d+ trip_details
\d+ expenses