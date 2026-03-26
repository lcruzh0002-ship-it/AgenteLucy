// next-auth.d.ts  ← crear en la RAÍZ del proyecto (junto a package.json)
import "next-auth";
import "next-auth/jwt";
 
declare module "next-auth" {
  interface Session {
    accessToken?: string;
  }
}
 
declare module "next-auth/jwt" {
  interface JWT {
    accessToken?: string;
  }
}
 