-- 1️⃣ Rename the old enum type
ALTER TYPE accounttypeenum RENAME TO accounttypeenum_old;

-- 2️⃣ Create a new enum type with uppercase values
CREATE TYPE accounttypeenum AS ENUM ('ASSET','LIABILITY','EQUITY','REVENUE','EXPENSE');

-- 3️⃣ Alter table column to use new enum, mapping existing values
ALTER TABLE account
ALTER COLUMN account_type TYPE accounttypeenum
USING UPPER(account_type::text)::accounttypeenum;

-- 4️⃣ Drop the old enum type
DROP TYPE accounttypeenum_old;
