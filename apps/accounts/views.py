from rest_framework.response import Response
from rest_framework.views import APIView
from apps.accounts.serializers import CreateUserSerializer


class RegisterAPIView(APIView):
    serializer_class = CreateUserSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'success'}, status=201)
        return Response(serializer.errors, status=400)
