


SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;


COMMENT ON SCHEMA "public" IS 'standard public schema';



CREATE EXTENSION IF NOT EXISTS "pg_stat_statements" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "pgcrypto" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "supabase_vault" WITH SCHEMA "vault";






CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA "extensions";





SET default_tablespace = '';

SET default_table_access_method = "heap";


CREATE TABLE IF NOT EXISTS "public"."admin_logs" (
    "id" integer NOT NULL,
    "user_id" integer,
    "action" "text" NOT NULL,
    "target" "text",
    "logged_at" timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE "public"."admin_logs" OWNER TO "postgres";


CREATE SEQUENCE IF NOT EXISTS "public"."admin_logs_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE "public"."admin_logs_id_seq" OWNER TO "postgres";


ALTER SEQUENCE "public"."admin_logs_id_seq" OWNED BY "public"."admin_logs"."id";



CREATE TABLE IF NOT EXISTS "public"."challenges" (
    "id" integer NOT NULL,
    "title" character varying(100) NOT NULL,
    "category" character varying(50) NOT NULL,
    "difficulty" character varying(50) NOT NULL,
    "points" integer NOT NULL,
    "description" "text",
    "flag" character varying(255) NOT NULL,
    "file_url" character varying(255) DEFAULT NULL::character varying,
    "created_at" timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE "public"."challenges" OWNER TO "postgres";


CREATE SEQUENCE IF NOT EXISTS "public"."challenges_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE "public"."challenges_id_seq" OWNER TO "postgres";


ALTER SEQUENCE "public"."challenges_id_seq" OWNED BY "public"."challenges"."id";



CREATE TABLE IF NOT EXISTS "public"."login_logs" (
    "id" integer NOT NULL,
    "user_id" integer,
    "ip_address" character varying(45),
    "success" smallint DEFAULT 0,
    "attempted_at" timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE "public"."login_logs" OWNER TO "postgres";


CREATE SEQUENCE IF NOT EXISTS "public"."login_logs_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE "public"."login_logs_id_seq" OWNER TO "postgres";


ALTER SEQUENCE "public"."login_logs_id_seq" OWNED BY "public"."login_logs"."id";



CREATE TABLE IF NOT EXISTS "public"."platform_settings" (
    "id" integer NOT NULL,
    "event_name" character varying(255) DEFAULT 'DosaCTF 2026'::character varying,
    "event_status" character varying(50) DEFAULT 'Active'::character varying,
    "start_date" timestamp without time zone,
    "end_date" timestamp without time zone,
    "max_team_size" integer DEFAULT 4,
    "flag_cooldown" integer DEFAULT 60,
    "alert_email" character varying(255),
    "webhook_url" character varying(255),
    "auto_backup" character varying(50) DEFAULT 'Daily'::character varying,
    "retention" character varying(50) DEFAULT '30 Days'::character varying
);


ALTER TABLE "public"."platform_settings" OWNER TO "postgres";


CREATE SEQUENCE IF NOT EXISTS "public"."platform_settings_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE "public"."platform_settings_id_seq" OWNER TO "postgres";


ALTER SEQUENCE "public"."platform_settings_id_seq" OWNED BY "public"."platform_settings"."id";



CREATE TABLE IF NOT EXISTS "public"."solves" (
    "id" integer NOT NULL,
    "user_id" integer NOT NULL,
    "challenge_id" integer NOT NULL,
    "solved_at" timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE "public"."solves" OWNER TO "postgres";


CREATE SEQUENCE IF NOT EXISTS "public"."solves_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE "public"."solves_id_seq" OWNER TO "postgres";


ALTER SEQUENCE "public"."solves_id_seq" OWNED BY "public"."solves"."id";



CREATE TABLE IF NOT EXISTS "public"."users" (
    "id" integer NOT NULL,
    "username" character varying(50) NOT NULL,
    "email" character varying(120) NOT NULL,
    "password" character varying(255) NOT NULL,
    "role" "text" DEFAULT 'player'::"text" NOT NULL,
    "status" "text" DEFAULT 'active'::"text" NOT NULL,
    "score" integer DEFAULT 0 NOT NULL,
    "avatar" character varying(4) DEFAULT NULL::character varying,
    "created_at" timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    "last_login" timestamp without time zone,
    "display_name" character varying(100),
    "avatar_style" character varying(100) DEFAULT 'linear-gradient(135deg, #1a0a3a, var(--blue))'::character varying
);


ALTER TABLE "public"."users" OWNER TO "postgres";


CREATE SEQUENCE IF NOT EXISTS "public"."users_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE "public"."users_id_seq" OWNER TO "postgres";


ALTER SEQUENCE "public"."users_id_seq" OWNED BY "public"."users"."id";



CREATE TABLE IF NOT EXISTS "public"."view_users" (
    "id" integer NOT NULL,
    "username" "text" NOT NULL,
    "email" "text" NOT NULL,
    "role" "text" DEFAULT 'Player'::"text",
    "status" "text" DEFAULT 'Active'::"text",
    "score" integer DEFAULT 0,
    "online_status" boolean DEFAULT false,
    "joined_at" timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE "public"."view_users" OWNER TO "postgres";


CREATE SEQUENCE IF NOT EXISTS "public"."view_users_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE "public"."view_users_id_seq" OWNER TO "postgres";


ALTER SEQUENCE "public"."view_users_id_seq" OWNED BY "public"."view_users"."id";



ALTER TABLE ONLY "public"."admin_logs" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."admin_logs_id_seq"'::"regclass");



ALTER TABLE ONLY "public"."challenges" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."challenges_id_seq"'::"regclass");



ALTER TABLE ONLY "public"."login_logs" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."login_logs_id_seq"'::"regclass");



ALTER TABLE ONLY "public"."platform_settings" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."platform_settings_id_seq"'::"regclass");



ALTER TABLE ONLY "public"."solves" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."solves_id_seq"'::"regclass");



ALTER TABLE ONLY "public"."users" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."users_id_seq"'::"regclass");



ALTER TABLE ONLY "public"."view_users" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."view_users_id_seq"'::"regclass");



ALTER TABLE ONLY "public"."admin_logs"
    ADD CONSTRAINT "admin_logs_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."challenges"
    ADD CONSTRAINT "challenges_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."login_logs"
    ADD CONSTRAINT "login_logs_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."platform_settings"
    ADD CONSTRAINT "platform_settings_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."solves"
    ADD CONSTRAINT "solves_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."solves"
    ADD CONSTRAINT "solves_user_id_challenge_id_key" UNIQUE ("user_id", "challenge_id");



ALTER TABLE ONLY "public"."users"
    ADD CONSTRAINT "users_email_key" UNIQUE ("email");



ALTER TABLE ONLY "public"."users"
    ADD CONSTRAINT "users_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."users"
    ADD CONSTRAINT "users_username_key" UNIQUE ("username");



ALTER TABLE ONLY "public"."view_users"
    ADD CONSTRAINT "view_users_email_key" UNIQUE ("email");



ALTER TABLE ONLY "public"."view_users"
    ADD CONSTRAINT "view_users_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."admin_logs"
    ADD CONSTRAINT "admin_logs_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "public"."users"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."login_logs"
    ADD CONSTRAINT "login_logs_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "public"."users"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."solves"
    ADD CONSTRAINT "solves_challenge_id_fkey" FOREIGN KEY ("challenge_id") REFERENCES "public"."challenges"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."solves"
    ADD CONSTRAINT "solves_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "public"."users"("id") ON DELETE CASCADE;



CREATE POLICY "Allow public read" ON "public"."view_users" FOR SELECT USING (true);



ALTER TABLE "public"."view_users" ENABLE ROW LEVEL SECURITY;




ALTER PUBLICATION "supabase_realtime" OWNER TO "postgres";


GRANT USAGE ON SCHEMA "public" TO "postgres";
GRANT USAGE ON SCHEMA "public" TO "anon";
GRANT USAGE ON SCHEMA "public" TO "authenticated";
GRANT USAGE ON SCHEMA "public" TO "service_role";





































































































































































GRANT ALL ON TABLE "public"."admin_logs" TO "anon";
GRANT ALL ON TABLE "public"."admin_logs" TO "authenticated";
GRANT ALL ON TABLE "public"."admin_logs" TO "service_role";



GRANT ALL ON SEQUENCE "public"."admin_logs_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."admin_logs_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."admin_logs_id_seq" TO "service_role";



GRANT ALL ON TABLE "public"."challenges" TO "anon";
GRANT ALL ON TABLE "public"."challenges" TO "authenticated";
GRANT ALL ON TABLE "public"."challenges" TO "service_role";



GRANT ALL ON SEQUENCE "public"."challenges_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."challenges_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."challenges_id_seq" TO "service_role";



GRANT ALL ON TABLE "public"."login_logs" TO "anon";
GRANT ALL ON TABLE "public"."login_logs" TO "authenticated";
GRANT ALL ON TABLE "public"."login_logs" TO "service_role";



GRANT ALL ON SEQUENCE "public"."login_logs_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."login_logs_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."login_logs_id_seq" TO "service_role";



GRANT ALL ON TABLE "public"."platform_settings" TO "anon";
GRANT ALL ON TABLE "public"."platform_settings" TO "authenticated";
GRANT ALL ON TABLE "public"."platform_settings" TO "service_role";



GRANT ALL ON SEQUENCE "public"."platform_settings_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."platform_settings_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."platform_settings_id_seq" TO "service_role";



GRANT ALL ON TABLE "public"."solves" TO "anon";
GRANT ALL ON TABLE "public"."solves" TO "authenticated";
GRANT ALL ON TABLE "public"."solves" TO "service_role";



GRANT ALL ON SEQUENCE "public"."solves_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."solves_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."solves_id_seq" TO "service_role";



GRANT ALL ON TABLE "public"."users" TO "anon";
GRANT ALL ON TABLE "public"."users" TO "authenticated";
GRANT ALL ON TABLE "public"."users" TO "service_role";



GRANT ALL ON SEQUENCE "public"."users_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."users_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."users_id_seq" TO "service_role";



GRANT ALL ON TABLE "public"."view_users" TO "anon";
GRANT ALL ON TABLE "public"."view_users" TO "authenticated";
GRANT ALL ON TABLE "public"."view_users" TO "service_role";



GRANT ALL ON SEQUENCE "public"."view_users_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."view_users_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."view_users_id_seq" TO "service_role";









ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "service_role";






ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "service_role";






ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES TO "service_role";































