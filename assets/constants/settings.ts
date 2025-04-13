import { Setting } from "../types/Setting"


export const SETTINGDATA : Setting[] = [
    {
      section: "Account",
      items: [
        {
          title: "My Account",
          description: "",
          icon: "person-circle-sharp", 
        },
        {
          title: "Licence",
          description:"",
          icon: "key",
          href: "/",
        },
      ],
    },
    {
      section: "Help",
      items: [
        {
          title: "Q&A",
          description: "",
          icon: "help-circle-outline",
        },
        {
          title: "About",
          description: "",
          icon: "information-circle-outline",
        },
      ],
    },
    {
      section: "Actions",
      items: [
        {
          title: "Log Out",
          description: "",
          icon: "log-out-outline",
          action: "logout",
          logoutStyle: true,
        },
      ],
    },
  ];