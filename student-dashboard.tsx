import Image from "next/image"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import {
  MessageCircle,
  Bell,
  CreditCard,
  Calendar,
  Users,
  DollarSign,
  Check,
  Building,
  User,
  Phone,
  Mail,
  Home,
} from "lucide-react"
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPersonHalfDress } from '@fortawesome/free-solid-svg-icons';

export default function Component() {
  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div className="text-2xl font-bold text-teal-700">NEXTUTE</div>
        <div className="flex items-center gap-4">
          <div className="w-10 h-10 bg-teal-100 rounded-full flex items-center justify-center">
            <MessageCircle className="w-5 h-5 text-teal-600" />
          </div>
          <div className="w-10 h-10 bg-teal-100 rounded-full flex items-center justify-center">
            <Bell className="w-5 h-5 text-teal-600" />
          </div>
        </div>
      </div>

      {/* Main Profile Section */}
      <Card className="mb-6 bg-green-50 border-green-200">
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="relative">
                <div className="w-20 h-20 rounded-full border-4 border-green-400 overflow-hidden">
                  <Image
                    src="/profile-avatar.png"
                    alt="Profile"
                    width={80}
                    height={80}
                    className="w-full h-full object-cover"
                  />
                </div>
              </div>
              <div>
                <h1 className="text-3xl font-bold text-gray-800 mb-1">Hello, Khushi!</h1>
                <p className="text-gray-600">Nextute</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className="relative w-20 h-20">
                <svg className="w-20 h-20 transform -rotate-90" viewBox="0 0 36 36">
                  <path
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    fill="none"
                    stroke="#e5e7eb"
                    strokeWidth="2"
                  />
                  <path
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    fill="none"
                    stroke="#10b981"
                    strokeWidth="2"
                    strokeDasharray="40, 100"
                  />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-lg font-bold text-gray-700">40%</span>
                </div>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-gray-800">40%</div>
                <div className="text-sm text-gray-600">profile completed</div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column */}
        <div className="space-y-4">
          {/* Student ID */}
          <Card className="bg-green-50 border-green-200">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <CreditCard className="w-5 h-5 text-teal-600" />
                <div>
                  <div className="text-sm font-medium text-gray-700">student_id</div>
                  <div className="text-lg font-semibold text-gray-800">Nx_123</div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Gender */}
          <Card className="bg-green-50 border-green-200">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <FontAwesomeIcon icon={faPersonHalfDress} className="w-5 h-5 text-pink-500" />
                <div>
                  <div className="text-sm font-medium text-gray-700">Gender</div>
                  <div className="text-lg font-semibold text-gray-800">female</div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* DOB */}
          <Card className="bg-green-50 border-green-200">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <Calendar className="w-5 h-5 text-teal-600" />
                <div>
                  <div className="text-sm font-medium text-gray-700">DOB</div>
                  <div className="text-lg text-gray-500">dd/mm/yyyy</div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Memberships */}
          <Card className="bg-green-50 border-green-200">
            <CardContent className="p-4">
              <div className="text-sm font-medium text-gray-700 mb-3">memberships</div>
              <div className="bg-white rounded-lg p-3 border border-gray-200">
                <div className="text-sm text-gray-600">• personalized</div>
                <div className="text-sm font-medium text-gray-800">Mentorship</div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Center Column */}
        <div className="space-y-4">
          {/* Address */}
          <Card className="bg-green-50 border-green-200">
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Home className="w-5 h-5 text-teal-600" />
                  <span className="font-medium text-gray-700">Address</span>
                </div>
                <Button variant="ghost" size="sm" className="text-gray-500 hover:text-gray-700">
                  Edit
                </Button>
              </div>
              <div className="text-gray-400 text-sm">enter your full address</div>
            </CardContent>
          </Card>

          {/* Guardian */}
          <Card className="bg-green-50 border-green-200">
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Users className="w-5 h-5 text-teal-600" />
                  <span className="font-medium text-gray-700">Guardian</span>
                </div>
                <Button variant="ghost" size="sm" className="text-gray-500 hover:text-gray-700">
                  Edit
                </Button>
              </div>
              <div className="text-gray-400 text-sm">name</div>
            </CardContent>
          </Card>

          {/* Payment Status */}
          <Card className="bg-green-50 border-green-200">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-4">
                <DollarSign className="w-5 h-5 text-teal-600" />
                <span className="font-medium text-gray-700">Payment status</span>
              </div>
              <div className="flex flex-col items-center">
                <div className="w-16 h-16 bg-teal-600 rounded-full flex items-center justify-center mb-2">
                  <Check className="w-8 h-8 text-white" />
                </div>
                <div className="text-lg font-bold text-gray-800">PAID</div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Column */}
        <div className="space-y-4">
          {/* Institute Searched */}
          <Card className="bg-green-50 border-green-200">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-4">
                <Building className="w-5 h-5 text-teal-600" />
                <span className="font-medium text-gray-700">Institute searched</span>
              </div>
              <div className="space-y-2">
                <div className="bg-white rounded-full px-4 py-2 border border-gray-200">
                  <span className="text-sm text-gray-700">• Alpha classes</span>
                </div>
                <div className="bg-white rounded-full px-4 py-2 border border-gray-200">
                  <span className="text-sm text-gray-700">• BETA classes</span>
                </div>
                <div className="bg-white rounded-full px-4 py-2 border border-gray-200">
                  <span className="text-sm text-gray-700">• GAMA classes</span>
                </div>
                <div className="bg-white rounded-full px-4 py-2 border border-gray-200">
                  <span className="text-sm text-gray-700">• ZETA classes</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Contact Info */}
          <Card className="bg-green-50 border-green-200">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-4">
                <User className="w-5 h-5 text-teal-600" />
                <span className="font-medium text-gray-700">Contact Info</span>
              </div>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Phone className="w-4 h-4 text-teal-600" />
                    <div>
                      <div className="text-xs text-gray-500">phone number</div>
                      <div className="text-sm font-medium text-gray-800">+91 9999999999</div>
                    </div>
                  </div>
                  <Button variant="ghost" size="sm" className="text-gray-500 hover:text-gray-700">
                    Edit
                  </Button>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Mail className="w-4 h-4 text-teal-600" />
                    <div>
                      <div className="text-xs text-gray-500">email address</div>
                      <div className="text-sm font-medium text-gray-800">khushi420@gmail.com</div>
                    </div>
                  </div>
                  <Button variant="ghost" size="sm" className="text-gray-500 hover:text-gray-700">
                    Edit
                  </Button>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Phone className="w-4 h-4 text-teal-600" />
                    <div>
                      <div className="text-xs text-gray-500">guardian phone number</div>
                      <div className="text-sm font-medium text-gray-800">+91 9999999999</div>
                    </div>
                  </div>
                  <Button variant="ghost" size="sm" className="text-gray-500 hover:text-gray-700">
                    Edit
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
